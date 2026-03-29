from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.domain.enums import LoanType, Permission
from app.models import User
from app.schemas import APISuccessResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/dashboard_info", response_model=APISuccessResponse)
def dashboard_info(
    year: int | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    loan_type: LoanType | None = None,
    user: User = Depends(require_permission(Permission.REVIEW_BSI_REPORT)),
    db: Session = Depends(get_db),
):
    try:
        stats = dashboard_service.get_dashboard_statistics(
            db,
            enterprise_id=user.enterprise_id,
            year=year,
            month=month,
            loan_type=loan_type.value if loan_type else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    latest = dashboard_service.latest_signals(db, enterprise_id=user.enterprise_id, limit=5)
    stats["latest_signals_preview"] = latest
    return APISuccessResponse(http_status_code=200, message="Dashboard info retrieved successfully", result=stats)


@router.get("/me", response_model=APISuccessResponse)
def me(user: User = Depends(require_permission(Permission.REVIEW_BSI_REPORT))):
    return APISuccessResponse(
        http_status_code=200,
        message="Current principal",
        result={"user_id": user.id, "email": user.email, "enterprise_id": user.enterprise_id, "role": user.role},
    )
