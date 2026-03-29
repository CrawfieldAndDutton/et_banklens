from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.domain.enums import Permission, SignalSeverity
from app.models import Customer, Signal, User
from app.schemas import APISuccessResponse

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.get("/latest", response_model=APISuccessResponse)
def latest_signals(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    severity: SignalSeverity | None = None,
    user: User = Depends(require_permission(Permission.REVIEW_BSI_REPORT)),
    db: Session = Depends(get_db),
):
    q = select(Signal).where(Signal.enterprise_id == user.enterprise_id)
    if severity is not None:
        q = q.where(Signal.severity == severity.value)
    q = q.order_by(Signal.created_at.desc())
    rows = list(db.execute(q.offset((page - 1) * size).limit(size)).scalars().all())
    items = [
        {
            "signal_id": s.id,
            "customer_id": s.customer_id,
            "run_id": s.run_id,
            "signal_type": s.signal_type,
            "severity": s.severity,
            "narrative": s.narrative,
            "created_at": s.created_at.isoformat(),
        }
        for s in rows
    ]
    return APISuccessResponse(http_status_code=200, message="Latest signals", result={"page": page, "size": size, "items": items})


@router.get("/search", response_model=APISuccessResponse)
def search_signals(
    qtext: str = Query(..., min_length=1, max_length=64, description="Match signal_type or narrative (case-insensitive)"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user: User = Depends(require_permission(Permission.REVIEW_BSI_REPORT)),
    db: Session = Depends(get_db),
):
    needle = f"%{qtext.lower()}%"
    q = (
        select(Signal)
        .where(Signal.enterprise_id == user.enterprise_id)
        .where(
            or_(
                func.lower(Signal.signal_type).like(needle),
                func.lower(Signal.narrative).like(needle),
            )
        )
        .order_by(Signal.created_at.desc())
    )
    rows = list(db.execute(q.offset((page - 1) * size).limit(size)).scalars().all())
    items = [
        {
            "signal_id": s.id,
            "customer_id": s.customer_id,
            "signal_type": s.signal_type,
            "severity": s.severity,
            "narrative": s.narrative,
        }
        for s in rows
    ]
    return APISuccessResponse(http_status_code=200, message="Signal search results", result={"query": qtext, "items": items})


@router.get("/customers/{customer_id}", response_model=APISuccessResponse)
def signals_for_customer(
    customer_id: int,
    user: User = Depends(require_permission(Permission.REVIEW_BSI_REPORT)),
    db: Session = Depends(get_db),
):
    c = db.get(Customer, customer_id)
    if c is None or c.enterprise_id != user.enterprise_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    rows = list(
        db.execute(
            select(Signal)
            .where(Signal.customer_id == customer_id, Signal.enterprise_id == user.enterprise_id)
            .order_by(Signal.created_at.desc())
        )
        .scalars()
        .all()
    )
    return APISuccessResponse(
        http_status_code=200,
        message="Signals for customer",
        result={
            "customer_id": customer_id,
            "count": len(rows),
            "items": [
                {
                    "signal_id": r.id,
                    "run_id": r.run_id,
                    "signal_type": r.signal_type,
                    "severity": r.severity,
                    "narrative": r.narrative,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ],
        },
    )
