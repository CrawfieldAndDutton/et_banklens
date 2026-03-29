"""Append-only audit trail in its own DB session so denials and failures remain provable."""

from __future__ import annotations

import json
from typing import Any

from app.database import SessionLocal
from app.domain.enums import AuditEventType, RetentionClass
from app.models import AuditEvent


def record_audit(
    *,
    enterprise_id: int,
    actor_user_id: int | None,
    correlation_id: str,
    event_type: AuditEventType,
    resource_type: str,
    resource_id: str,
    decision_code: str,
    rule_pack_version: str | None,
    inputs_redacted: dict[str, Any],
    outcome: dict[str, Any],
) -> int:
    row = AuditEvent(
        enterprise_id=enterprise_id,
        actor_user_id=actor_user_id,
        correlation_id=correlation_id,
        event_type=event_type.value,
        resource_type=resource_type,
        resource_id=resource_id,
        decision_code=decision_code,
        rule_pack_version=rule_pack_version,
        inputs_redacted_json=json.dumps(inputs_redacted, default=str),
        outcome_json=json.dumps({**outcome, "retention_class": RetentionClass.AUDIT_IMMUTABLE.value}, default=str),
    )
    with SessionLocal() as session:
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)
