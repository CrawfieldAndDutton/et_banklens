from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_correlation_id, get_current_user, require_permission
from app.domain.enums import AuditEventType, Permission
from app.models import BSIMonitoringRun, Customer, LoanAccount, User
from app.schemas import (
    APISuccessResponse,
    ConsentUpdateRequest,
    CustomerCreateRequest,
    CustomerCreatedResponse,
    MonitoredCustomerRow,
)
from app.services import audit_service
from app.services.pii import mask_phone, pan_hash, pan_last_four

router = APIRouter(prefix="/customers", tags=["Customers"])


def _latest_bsi_status(db: Session, customer_id: int) -> str | None:
    run = db.execute(
        select(BSIMonitoringRun)
        .where(BSIMonitoringRun.customer_id == customer_id)
        .order_by(BSIMonitoringRun.started_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    return run.status if run else None


@router.get("/monitored", response_model=APISuccessResponse)
def list_monitored_customers(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user: User = Depends(require_permission(Permission.REVIEW_BSI_REPORT)),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    base = Customer.enterprise_id == user.enterprise_id
    total = int(db.execute(select(func.count()).select_from(Customer).where(base)).scalar_one() or 0)
    q = select(Customer).where(base).order_by(Customer.id.asc())
    rows = list(db.execute(q.offset((page - 1) * size).limit(size)).scalars().all())
    out: list[MonitoredCustomerRow] = []
    for c in rows:
        loan = db.execute(select(LoanAccount).where(LoanAccount.customer_id == c.id)).scalar_one_or_none()
        out.append(
            MonitoredCustomerRow(
                customer_id=c.id,
                external_ref=c.external_ref,
                display_name=c.display_name,
                phone_masked=mask_phone(c.phone),
                pan_last4=c.pan_last_four,
                loan_type=c.loan_type,
                consent_monitoring=c.consent_monitoring,
                last_bsi_status=_latest_bsi_status(db, c.id),
                has_loan_snapshot=loan is not None,
            )
        )
    audit_service.record_audit(
        enterprise_id=user.enterprise_id,
        actor_user_id=user.id,
        correlation_id=correlation_id,
        event_type=AuditEventType.DATA_ACCESSED,
        resource_type="customer_list",
        resource_id=f"enterprise:{user.enterprise_id}",
        decision_code="LIST_MONITORED_CUSTOMERS",
        rule_pack_version=None,
        inputs_redacted={"page": page, "size": size, "total_estimate": total},
        outcome={"returned": len(out)},
    )
    return APISuccessResponse(
        http_status_code=200,
        message="Monitored customers retrieved successfully",
        result={"page": page, "size": size, "total": total, "items": [m.model_dump() for m in out]},
    )


@router.get("/{customer_id}", response_model=APISuccessResponse)
def get_customer_detail(
    customer_id: int,
    user: User = Depends(require_permission(Permission.REVIEW_BSI_REPORT)),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    c = db.get(Customer, customer_id)
    if c is None or c.enterprise_id != user.enterprise_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    loan = db.execute(select(LoanAccount).where(LoanAccount.customer_id == c.id)).scalar_one_or_none()
    audit_service.record_audit(
        enterprise_id=user.enterprise_id,
        actor_user_id=user.id,
        correlation_id=correlation_id,
        event_type=AuditEventType.DATA_ACCESSED,
        resource_type="customer",
        resource_id=str(c.id),
        decision_code="CUSTOMER_DETAIL_VIEW",
        rule_pack_version=None,
        inputs_redacted={"external_ref": c.external_ref},
        outcome={"masked_response": True},
    )
    payload = {
        "customer_id": c.id,
        "external_ref": c.external_ref,
        "display_name": c.display_name,
        "phone_masked": mask_phone(c.phone),
        "pan_last4": c.pan_last_four,
        "loan_type": c.loan_type,
        "consent_monitoring": c.consent_monitoring,
        "consent_recorded_at": c.consent_recorded_at.isoformat() if c.consent_recorded_at else None,
        "last_bsi_status": _latest_bsi_status(db, c.id),
        "loan_snapshot": None
        if loan is None
        else {
            "principal_outstanding": loan.principal_outstanding,
            "emi_amount": loan.emi_amount,
            "dpd_days": loan.dpd_days,
            "avg_monthly_inflow": loan.avg_monthly_inflow,
            "eod_negative_days_90d": loan.eod_negative_days_90d,
            "credit_score_delta_90d": loan.credit_score_delta_90d,
            "salary_proxy_delta_pct": loan.salary_proxy_delta_pct,
        },
    }
    return APISuccessResponse(http_status_code=200, message="Customer detail (PII minimised)", result=payload)


@router.post("", response_model=APISuccessResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CustomerCreateRequest,
    user: User = Depends(require_permission(Permission.CUSTOMER_CREATION)),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    ph = pan_hash(body.pan)
    if db.execute(
        select(Customer).where(Customer.enterprise_id == user.enterprise_id, Customer.external_ref == body.external_ref)
    ).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="external_ref already exists for tenant")
    if db.execute(select(Customer).where(Customer.enterprise_id == user.enterprise_id, Customer.pan_hash == ph)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Borrower identity hash already on file (duplicate PAN for this lender).",
        )
    from datetime import datetime, timezone

    c = Customer(
        enterprise_id=user.enterprise_id,
        external_ref=body.external_ref,
        display_name=body.display_name,
        pan_hash=ph,
        pan_last_four=pan_last_four(body.pan),
        phone=body.phone,
        email=str(body.email) if body.email else None,
        loan_type=body.loan_type.value,
        consent_monitoring=body.consent_monitoring,
        consent_recorded_at=datetime.now(timezone.utc) if body.consent_monitoring else None,
    )
    db.add(c)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict creating customer") from None
    db.refresh(c)
    if body.loan_snapshot:
        db.add(
            LoanAccount(
                customer_id=c.id,
                principal_outstanding=body.loan_snapshot.principal_outstanding,
                emi_amount=body.loan_snapshot.emi_amount,
                dpd_days=body.loan_snapshot.dpd_days,
                avg_monthly_inflow=body.loan_snapshot.avg_monthly_inflow,
                eod_negative_days_90d=body.loan_snapshot.eod_negative_days_90d,
                credit_score_delta_90d=body.loan_snapshot.credit_score_delta_90d,
                salary_proxy_delta_pct=body.loan_snapshot.salary_proxy_delta_pct,
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Loan snapshot conflict") from None

    audit_service.record_audit(
        enterprise_id=user.enterprise_id,
        actor_user_id=user.id,
        correlation_id=correlation_id,
        event_type=AuditEventType.CUSTOMER_CREATED,
        resource_type="customer",
        resource_id=str(c.id),
        decision_code="CUSTOMER_ONBOARDED",
        rule_pack_version=None,
        inputs_redacted={
            "external_ref": c.external_ref,
            "loan_type": c.loan_type,
            "consent_monitoring": c.consent_monitoring,
            "has_loan_snapshot": body.loan_snapshot is not None,
        },
        outcome={"customer_id": c.id},
    )
    resp = CustomerCreatedResponse(
        id=c.id,
        external_ref=c.external_ref,
        pan_last4=pan_last_four(body.pan),
        phone_masked=mask_phone(c.phone),
        consent_monitoring=c.consent_monitoring,
        loan_type=c.loan_type,
    )
    return APISuccessResponse(http_status_code=201, message="Customer created", result=resp.model_dump())


@router.patch("/{customer_id}/consent", response_model=APISuccessResponse)
def update_monitoring_consent(
    customer_id: int,
    body: ConsentUpdateRequest,
    user: User = Depends(require_permission(Permission.CUSTOMER_MODIFICATION)),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    c = db.get(Customer, customer_id)
    if c is None or c.enterprise_id != user.enterprise_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    from datetime import datetime, timezone

    prev = c.consent_monitoring
    c.consent_monitoring = body.consent_monitoring
    c.consent_recorded_at = datetime.now(timezone.utc) if body.consent_monitoring else None
    db.commit()
    audit_service.record_audit(
        enterprise_id=user.enterprise_id,
        actor_user_id=user.id,
        correlation_id=correlation_id,
        event_type=AuditEventType.CONSENT_RECORD_UPDATED,
        resource_type="customer",
        resource_id=str(c.id),
        decision_code="CONSENT_UPDATED",
        rule_pack_version=None,
        inputs_redacted={"previous": prev, "requested": body.consent_monitoring},
        outcome={"consent_monitoring": c.consent_monitoring},
    )
    return APISuccessResponse(
        http_status_code=200,
        message="Monitoring consent updated (purpose limitation)",
        result={"customer_id": c.id, "consent_monitoring": c.consent_monitoring},
    )
