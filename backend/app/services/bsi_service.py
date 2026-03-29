"""BSI monitoring run orchestration: guardrails → snapshot → rules → signals → audit."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.enums import AuditEventType, BSIStatus
from app.models import BSIMonitoringRun, Customer, LoanAccount, Signal, User
from app.services import audit_service
from app.services.genai_service import generate_bsi_executive_summary
from app.services.rules_engine import evaluate_rules, redacted_feature_snapshot


class BSIService:
    @staticmethod
    def trigger_for_customer(
        db: Session,
        *,
        actor: User,
        customer_id: int,
        correlation_id: str,
    ) -> BSIMonitoringRun:
        settings = get_settings()
        customer = db.get(Customer, customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        if customer.enterprise_id != actor.enterprise_id:
            audit_service.record_audit(
                enterprise_id=actor.enterprise_id,
                actor_user_id=actor.id,
                correlation_id=correlation_id,
                event_type=AuditEventType.GUARDRAIL_BLOCKED,
                resource_type="customer",
                resource_id=str(customer_id),
                decision_code="TENANT_MISMATCH",
                rule_pack_version=None,
                inputs_redacted={"attempted_customer_id": customer_id},
                outcome={"allowed": False, "reason": "Customer belongs to another enterprise"},
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        loan = db.execute(select(LoanAccount).where(LoanAccount.customer_id == customer_id)).scalar_one_or_none()

        if not customer.consent_monitoring:
            audit_service.record_audit(
                enterprise_id=actor.enterprise_id,
                actor_user_id=actor.id,
                correlation_id=correlation_id,
                event_type=AuditEventType.GUARDRAIL_BLOCKED,
                resource_type="customer",
                resource_id=str(customer_id),
                decision_code="CONSENT_MONITORING_REQUIRED",
                rule_pack_version=None,
                inputs_redacted={"consent_monitoring": False},
                outcome={"allowed": False, "regulatory_note": "Purpose limitation: monitoring requires recorded consent."},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Monitoring consent not recorded for this borrower (guardrail: purpose limitation).",
            )

        if loan is None:
            audit_service.record_audit(
                enterprise_id=actor.enterprise_id,
                actor_user_id=actor.id,
                correlation_id=correlation_id,
                event_type=AuditEventType.GUARDRAIL_BLOCKED,
                resource_type="customer",
                resource_id=str(customer_id),
                decision_code="NO_LOAN_SNAPSHOT",
                rule_pack_version=None,
                inputs_redacted={"customer_external_ref": customer.external_ref},
                outcome={"allowed": False},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No loan snapshot on file; cannot run BSI rules.",
            )

        in_flight = db.execute(
            select(BSIMonitoringRun).where(
                BSIMonitoringRun.customer_id == customer_id,
                BSIMonitoringRun.status == BSIStatus.IN_PROGRESS.value,
            )
        ).scalar_one_or_none()
        if in_flight is not None:
            audit_service.record_audit(
                enterprise_id=actor.enterprise_id,
                actor_user_id=actor.id,
                correlation_id=correlation_id,
                event_type=AuditEventType.GUARDRAIL_BLOCKED,
                resource_type="bsi_run",
                resource_id=str(in_flight.id),
                decision_code="PARALLEL_RUN_NOT_ALLOWED",
                rule_pack_version=None,
                inputs_redacted={"existing_run_id": in_flight.id},
                outcome={"allowed": False},
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A monitoring run is already in progress for this customer.",
            )

        audit_service.record_audit(
            enterprise_id=actor.enterprise_id,
            actor_user_id=actor.id,
            correlation_id=correlation_id,
            event_type=AuditEventType.BSI_TRIGGER_REQUESTED,
            resource_type="customer",
            resource_id=str(customer_id),
            decision_code="TRIGGER_ACCEPTED",
            rule_pack_version=settings.rule_pack_version,
            inputs_redacted={
                "customer_external_ref": customer.external_ref,
                "consent_monitoring": True,
                "has_loan_snapshot": True,
            },
            outcome={"accepted_for_processing": True, "guardrails_passed": ["tenant", "consent", "loan", "parallel"]},
        )

        loan_dict: dict[str, int] = {
            "dpd_days": loan.dpd_days,
            "emi_amount": loan.emi_amount,
            "avg_monthly_inflow": loan.avg_monthly_inflow,
            "eod_negative_days_90d": loan.eod_negative_days_90d,
            "credit_score_delta_90d": loan.credit_score_delta_90d,
            "salary_proxy_delta_pct": loan.salary_proxy_delta_pct,
        }
        snapshot = redacted_feature_snapshot(
            customer_external_ref=customer.external_ref,
            loan=loan_dict,
            rule_pack_version=settings.rule_pack_version,
        )

        run = BSIMonitoringRun(
            enterprise_id=customer.enterprise_id,
            customer_id=customer.id,
            status=BSIStatus.IN_PROGRESS.value,
            correlation_id=correlation_id or str(uuid.uuid4()),
            triggered_by_user_id=actor.id,
            input_snapshot_json=snapshot,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

        audit_service.record_audit(
            enterprise_id=actor.enterprise_id,
            actor_user_id=actor.id,
            correlation_id=correlation_id,
            event_type=AuditEventType.BSI_RUN_STATE_CHANGED,
            resource_type="bsi_run",
            resource_id=str(run.id),
            decision_code="STATUS_IN_PROGRESS",
            rule_pack_version=settings.rule_pack_version,
            inputs_redacted={"snapshot_sha256": None},
            outcome={"status": BSIStatus.IN_PROGRESS.value},
        )

        try:
            evaluations, risk, dpd_bucket = evaluate_rules(
                rule_pack_version=settings.rule_pack_version,
                customer_ref=customer.external_ref,
                **loan_dict,
            )
            for ev in evaluations:
                audit_service.record_audit(
                    enterprise_id=actor.enterprise_id,
                    actor_user_id=actor.id,
                    correlation_id=correlation_id,
                    event_type=AuditEventType.AGENT_RULE_EVALUATED,
                    resource_type="bsi_run",
                    resource_id=str(run.id),
                    decision_code=ev.rule_id,
                    rule_pack_version=settings.rule_pack_version,
                    inputs_redacted=ev.inputs_used,
                    outcome={
                        "matched": ev.matched,
                        "signal_type": ev.signal_type.value if ev.signal_type else None,
                        "severity": ev.severity.value if ev.severity else None,
                        "narrative": ev.narrative,
                    },
                )
                if ev.matched and ev.signal_type and ev.severity:
                    db.add(
                        Signal(
                            run_id=run.id,
                            enterprise_id=customer.enterprise_id,
                            customer_id=customer.id,
                            signal_type=ev.signal_type.value,
                            severity=ev.severity.value,
                            narrative=ev.narrative or "",
                        )
                    )

            run.status = BSIStatus.COMPLETED.value
            run.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(run)

            final_outcome: dict[str, Any] = {
                "risk_level": risk.value,
                "dpd_bucket": dpd_bucket.value,
                "signals_emitted": sum(1 for e in evaluations if e.matched and e.signal_type),
            }
            audit_service.record_audit(
                enterprise_id=actor.enterprise_id,
                actor_user_id=actor.id,
                correlation_id=correlation_id,
                event_type=AuditEventType.AGENT_DECISION_FINAL,
                resource_type="bsi_run",
                resource_id=str(run.id),
                decision_code="RUN_COMPLETED",
                rule_pack_version=settings.rule_pack_version,
                inputs_redacted={"evaluated_rules": [e.rule_id for e in evaluations]},
                outcome=final_outcome,
            )

            signals_for_model = [
                {
                    "signal_type": ev.signal_type.value,
                    "severity": ev.severity.value,
                    "narrative": ev.narrative,
                }
                for ev in evaluations
                if ev.matched and ev.signal_type and ev.severity
            ]
            summary, model_used = generate_bsi_executive_summary(
                enterprise_id=actor.enterprise_id,
                actor_user_id=actor.id,
                correlation_id=correlation_id,
                run_id=run.id,
                rule_pack_version=settings.rule_pack_version,
                input_snapshot_json=snapshot,
                risk_level=risk.value,
                dpd_bucket=dpd_bucket.value,
                signals_for_model=signals_for_model,
            )
            if summary and model_used:
                run.gen_ai_summary = summary
                run.gen_ai_model = model_used
                db.commit()
                db.refresh(run)

            return run
        except Exception as exc:
            db.rollback()
            row = db.get(BSIMonitoringRun, run_id)
            if row is not None:
                row.status = BSIStatus.FAILED.value
                row.error_message = str(exc)[:2000]
                row.completed_at = datetime.now(timezone.utc)
                db.commit()
            audit_service.record_audit(
                enterprise_id=actor.enterprise_id,
                actor_user_id=actor.id,
                correlation_id=correlation_id,
                event_type=AuditEventType.BSI_RUN_STATE_CHANGED,
                resource_type="bsi_run",
                resource_id=str(run_id),
                decision_code="STATUS_FAILED",
                rule_pack_version=settings.rule_pack_version,
                inputs_redacted={},
                outcome={"error_class": type(exc).__name__},
            )
            raise exc
