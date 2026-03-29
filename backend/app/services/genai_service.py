"""
Generative AI layer: supplements deterministic BSI rules with narrative (OpenAI).

Guardrails:
- Prompts contain only structured, redacted JSON (same shape as `input_snapshot` + signal list).
- No borrower names, phone, email, or PAN in the model payload.
- Every attempt is audit-logged; failures never roll back the completed rules run.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.domain.enums import AuditEventType
from app.services import audit_service


def _prompt_fingerprint(system_prompt: str, user_message: str) -> str:
    h = hashlib.sha256(f"{system_prompt}\n---\n{user_message}".encode("utf-8")).hexdigest()
    return h[:24]


def generate_bsi_executive_summary(
    *,
    enterprise_id: int,
    actor_user_id: int,
    correlation_id: str,
    run_id: int,
    rule_pack_version: str,
    input_snapshot_json: str,
    risk_level: str,
    dpd_bucket: str,
    signals_for_model: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    """
    Returns (summary_text, model_name_used) or (None, None) if skipped/failed.
    """
    settings = get_settings()

    if not settings.gen_ai_after_bsi:
        audit_service.record_audit(
            enterprise_id=enterprise_id,
            actor_user_id=actor_user_id,
            correlation_id=correlation_id,
            event_type=AuditEventType.GEN_AI_SKIPPED,
            resource_type="bsi_run",
            resource_id=str(run_id),
            decision_code="GEN_AI_DISABLED",
            rule_pack_version=rule_pack_version,
            inputs_redacted={},
            outcome={"reason": "GEN_AI_AFTER_BSI=false"},
        )
        return None, None

    key = (settings.openai_api_key or "").strip()
    if not key:
        audit_service.record_audit(
            enterprise_id=enterprise_id,
            actor_user_id=actor_user_id,
            correlation_id=correlation_id,
            event_type=AuditEventType.GEN_AI_SKIPPED,
            resource_type="bsi_run",
            resource_id=str(run_id),
            decision_code="NO_OPENAI_API_KEY",
            rule_pack_version=rule_pack_version,
            inputs_redacted={},
            outcome={"reason": "OPENAI_API_KEY not set"},
        )
        return None, None

    try:
        snapshot_obj = json.loads(input_snapshot_json or "{}")
    except json.JSONDecodeError:
        snapshot_obj = {"parse_error": True}

    system_prompt = (
        "You are a senior credit risk analyst assistant for an Indian NBFC. "
        "You receive ONLY structured JSON derived from an internal rules engine (no PII). "
        "The deterministic rule engine is authoritative for which signals fired; your output must not "
        "contradict that JSON or invent metrics. "
        "Respond in clear Markdown with exactly two sections: "
        "## Executive summary\n and ## Suggested next actions\n. "
        "Keep total length under 400 words. Tone: professional, cautious, compliance-aware."
    )

    user_payload = {
        "rule_pack_version": rule_pack_version,
        "aggregated_risk_level": risk_level,
        "dpd_outlook_bucket": dpd_bucket,
        "signals": signals_for_model,
        "redacted_feature_snapshot": snapshot_obj,
        "task": (
            "Summarise risk for a committee and propose operational next steps "
            "(e.g. outreach, restructuring consideration, documentation review). "
            "Explicitly state that decisions must align with internal policy and the rule engine output."
        ),
    }
    user_message = json.dumps(user_payload, ensure_ascii=False)
    fingerprint = _prompt_fingerprint(system_prompt, user_message)

    audit_service.record_audit(
        enterprise_id=enterprise_id,
        actor_user_id=actor_user_id,
        correlation_id=correlation_id,
        event_type=AuditEventType.GEN_AI_INVOKED,
        resource_type="bsi_run",
        resource_id=str(run_id),
        decision_code="OPENAI_CHAT_COMPLETION",
        rule_pack_version=rule_pack_version,
        inputs_redacted={
            "model": settings.openai_model,
            "prompt_fingerprint_sha256_prefix": fingerprint,
            "user_message_chars": len(user_message),
            "signal_count": len(signals_for_model),
        },
        outcome={"provider": "openai", "note": "Full prompt not stored; fingerprint only."},
    )

    client_kwargs: dict[str, Any] = {"api_key": key, "timeout": settings.openai_timeout_seconds}
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url.strip()
    client = OpenAI(**client_kwargs)

    t0 = time.perf_counter()
    try:
        completion = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.25,
            max_tokens=900,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)
        choice = completion.choices[0].message
        text = (choice.content or "").strip()
        model_used = completion.model or settings.openai_model
        finish = getattr(completion.choices[0], "finish_reason", None)
        usage = completion.usage
        usage_out: dict[str, Any] = {}
        if usage is not None:
            usage_out = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }

        audit_service.record_audit(
            enterprise_id=enterprise_id,
            actor_user_id=actor_user_id,
            correlation_id=correlation_id,
            event_type=AuditEventType.GEN_AI_COMPLETED,
            resource_type="bsi_run",
            resource_id=str(run_id),
            decision_code="OPENAI_CHAT_COMPLETION",
            rule_pack_version=rule_pack_version,
            inputs_redacted={
                "model": model_used,
                "prompt_fingerprint_sha256_prefix": fingerprint,
                "latency_ms": latency_ms,
            },
            outcome={
                **usage_out,
                "finish_reason": finish,
                "response_chars": len(text),
                "retention_note": "Store full summary on BSIMonitoringRun.gen_ai_summary for replay.",
            },
        )
        return text or None, model_used
    except Exception as exc:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        audit_service.record_audit(
            enterprise_id=enterprise_id,
            actor_user_id=actor_user_id,
            correlation_id=correlation_id,
            event_type=AuditEventType.GEN_AI_FAILED,
            resource_type="bsi_run",
            resource_id=str(run_id),
            decision_code="OPENAI_ERROR",
            rule_pack_version=rule_pack_version,
            inputs_redacted={
                "model": settings.openai_model,
                "prompt_fingerprint_sha256_prefix": fingerprint,
                "latency_ms": latency_ms,
            },
            outcome={"error_class": type(exc).__name__, "message": str(exc)[:500]},
        )
        return None, None
