from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_correlation_id, require_permission
from app.domain.enums import Permission
from app.models import BSIMonitoringRun, User
from app.schemas import APISuccessResponse
from app.services.bsi_service import BSIService

router = APIRouter(prefix="/bsi", tags=["BSI Monitoring"])


@router.post(
    "/customers/{customer_id}/runs",
    response_model=APISuccessResponse,
    status_code=status.HTTP_201_CREATED,
)
def trigger_bsi_run(
    customer_id: int,
    user: User = Depends(require_permission(Permission.TRIGGER_BSI_PROCESS)),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    run = BSIService.trigger_for_customer(db, actor=user, customer_id=customer_id, correlation_id=correlation_id)
    return APISuccessResponse(
        http_status_code=201,
        message="BSI monitoring run completed (deterministic rules + optional generative summary)",
        result={
            "run_id": run.id,
            "customer_id": run.customer_id,
            "status": run.status,
            "correlation_id": run.correlation_id,
            "input_snapshot_json": run.input_snapshot_json,
            "gen_ai_model": run.gen_ai_model,
            "gen_ai_summary": run.gen_ai_summary,
        },
    )


@router.get("/runs/{run_id}", response_model=APISuccessResponse)
def get_bsi_run(
    run_id: int,
    user: User = Depends(require_permission(Permission.REVIEW_BSI_REPORT)),
    db: Session = Depends(get_db),
):
    run = db.get(BSIMonitoringRun, run_id)
    if run is None or run.enterprise_id != user.enterprise_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BSI run not found")
    return APISuccessResponse(
        http_status_code=200,
        message="BSI run detail",
        result={
            "run_id": run.id,
            "customer_id": run.customer_id,
            "status": run.status,
            "correlation_id": run.correlation_id,
            "started_at": run.started_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "input_snapshot_json": run.input_snapshot_json,
            "error_message": run.error_message,
            "gen_ai_model": run.gen_ai_model,
            "gen_ai_summary": run.gen_ai_summary,
        },
    )
