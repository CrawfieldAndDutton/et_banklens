"""Orchestrate WhatsApp + email outbound with consent guardrails and audit."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.enums import AuditEventType, OmnichannelChannel, OutboundDeliveryStatus
from app.models import Customer, OutboundMessage, User
from app.services import audit_service
from app.services.email_delivery import send_email_smtp
from app.services.pii import mask_email, mask_phone, whatsapp_recipient_digits
from app.services.whatsapp_delivery import send_whatsapp_text


def send_outbound_message(
    db: Session,
    *,
    actor: User,
    correlation_id: str,
    customer_id: int,
    channel: OmnichannelChannel,
    subject: str | None,
    body: str,
) -> OutboundMessage:
    settings = get_settings()
    customer = db.get(Customer, customer_id)
    if customer is None or customer.enterprise_id != actor.enterprise_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    if not customer.consent_monitoring:
        audit_service.record_audit(
            enterprise_id=actor.enterprise_id,
            actor_user_id=actor.id,
            correlation_id=correlation_id,
            event_type=AuditEventType.GUARDRAIL_BLOCKED,
            resource_type="omnichannel",
            resource_id=str(customer_id),
            decision_code="CONSENT_REQUIRED_FOR_OUTBOUND",
            rule_pack_version=None,
            inputs_redacted={"channel": channel.value},
            outcome={"allowed": False},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Outbound contact requires recorded monitoring consent for this borrower.",
        )

    if channel == OmnichannelChannel.EMAIL:
        if not (customer.email or "").strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer has no email on file for this channel.",
            )
        if not (subject or "").strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="subject is required for email")
        dest_masked = mask_email(customer.email)
    elif channel == OmnichannelChannel.WHATSAPP:
        wa_to = whatsapp_recipient_digits(customer.phone)
        if len(wa_to) < 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone for WhatsApp routing")
        dest_masked = mask_phone(customer.phone)
    else:
        raise HTTPException(status_code=400, detail="Unsupported channel")

    audit_service.record_audit(
        enterprise_id=actor.enterprise_id,
        actor_user_id=actor.id,
        correlation_id=correlation_id,
        event_type=AuditEventType.OMNICHANNEL_OUTBOUND_REQUESTED,
        resource_type="customer",
        resource_id=str(customer_id),
        decision_code=f"OUTBOUND_{channel.value.upper()}",
        rule_pack_version=None,
        inputs_redacted={
            "channel": channel.value,
            "destination_masked": dest_masked,
            "body_chars": len(body),
        },
        outcome={"phase": "before_provider_call"},
    )

    if channel == OmnichannelChannel.EMAIL:
        provider_id, err = send_email_smtp(
            to_addr=customer.email.strip(),
            subject=subject.strip(),
            body=body,
            settings=settings,
        )
    else:
        provider_id, err = send_whatsapp_text(to_digits=wa_to, body=body, settings=settings)

    if err:
        status_val = OutboundDeliveryStatus.FAILED.value
    elif (provider_id or "").startswith("MOCK-"):
        status_val = OutboundDeliveryStatus.MOCKED.value
    else:
        status_val = OutboundDeliveryStatus.SENT.value

    row = OutboundMessage(
        enterprise_id=actor.enterprise_id,
        customer_id=customer.id,
        channel=channel.value,
        subject=subject.strip() if subject and channel == OmnichannelChannel.EMAIL else None,
        body=body,
        destination_masked=dest_masked,
        status=status_val,
        provider_reference=provider_id or None,
        error_message=err,
        correlation_id=correlation_id,
        triggered_by_user_id=actor.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    audit_service.record_audit(
        enterprise_id=actor.enterprise_id,
        actor_user_id=actor.id,
        correlation_id=correlation_id,
        event_type=AuditEventType.OMNICHANNEL_OUTBOUND_RESULT,
        resource_type="outbound_message",
        resource_id=str(row.id),
        decision_code=status_val,
        rule_pack_version=None,
        inputs_redacted={"channel": channel.value, "destination_masked": dest_masked},
        outcome={
            "provider_reference": (provider_id[:120] if provider_id else None),
            "error": (err[:500] if err else None),
        },
    )

    return row
