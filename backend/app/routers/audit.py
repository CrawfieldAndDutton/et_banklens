from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_permission
from app.domain.enums import AuditEventType, Permission
from app.models import AuditEvent, User
from app.schemas import APISuccessResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/events", response_model=APISuccessResponse)
def list_audit_events(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    event_type: AuditEventType | None = None,
    correlation_id: str | None = Query(None, max_length=128),
    user: User = Depends(require_permission(Permission.AUDIT_AI_AGENT_CALL_REPORT)),
    db: Session = Depends(get_db),
):
    q = select(AuditEvent).where(AuditEvent.enterprise_id == user.enterprise_id).order_by(AuditEvent.id.desc())
    if event_type is not None:
        q = q.where(AuditEvent.event_type == event_type.value)
    if correlation_id:
        q = q.where(AuditEvent.correlation_id == correlation_id.strip())
    rows = list(db.execute(q.offset((page - 1) * size).limit(size)).scalars().all())
    items = []
    for r in rows:
        try:
            inputs_obj = json.loads(r.inputs_redacted_json or "{}")
            outcome_obj = json.loads(r.outcome_json or "{}")
        except json.JSONDecodeError:
            inputs_obj = {}
            outcome_obj = {"parse_error": True}
        items.append(
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "event_type": r.event_type,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "decision_code": r.decision_code,
                "rule_pack_version": r.rule_pack_version,
                "correlation_id": r.correlation_id,
                "actor_user_id": r.actor_user_id,
                "inputs_redacted": inputs_obj,
                "outcome": outcome_obj,
            }
        )
    return APISuccessResponse(
        http_status_code=200,
        message="Immutable audit trail (append-only store)",
        result={"page": page, "size": size, "items": items},
    )


@router.get("/events/{event_id}", response_model=APISuccessResponse)
def get_audit_event(
    event_id: int,
    user: User = Depends(require_permission(Permission.AUDIT_AI_AGENT_CALL_REPORT)),
    db: Session = Depends(get_db),
):
    r = db.get(AuditEvent, event_id)
    if r is None or r.enterprise_id != user.enterprise_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit event not found")
    try:
        inputs_obj = json.loads(r.inputs_redacted_json or "{}")
        outcome_obj = json.loads(r.outcome_json or "{}")
    except json.JSONDecodeError:
        inputs_obj = {}
        outcome_obj = {}
    return APISuccessResponse(
        http_status_code=200,
        message="Audit event detail",
        result={
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "event_type": r.event_type,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "decision_code": r.decision_code,
            "rule_pack_version": r.rule_pack_version,
            "correlation_id": r.correlation_id,
            "actor_user_id": r.actor_user_id,
            "inputs_redacted": inputs_obj,
            "outcome": outcome_obj,
        },
    )
