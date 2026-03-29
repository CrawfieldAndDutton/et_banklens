"""SMTP outbound (TLS). Returns (provider_message_id_or_mock, error_message)."""

from __future__ import annotations

import smtplib
import uuid
from email.message import EmailMessage

from app.config import Settings


def send_email_smtp(
    *,
    to_addr: str,
    subject: str,
    body: str,
    settings: Settings,
) -> tuple[str, str | None]:
    if not (settings.smtp_host or "").strip() or not (settings.smtp_from_email or "").strip():
        return f"MOCK-EMAIL-{uuid.uuid4().hex[:12]}", None

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email.strip()
    msg["To"] = to_addr.strip()
    msg.set_content(body, charset="utf-8")

    try:
        if settings.smtp_use_tls:
            with smtplib.SMTP(settings.smtp_host.strip(), settings.smtp_port, timeout=45) as smtp:
                smtp.starttls()
                user = (settings.smtp_user or "").strip()
                if user:
                    smtp.login(user, settings.smtp_password or "")
                smtp.send_message(msg)
        else:
            with smtplib.SMTP_SSL(settings.smtp_host.strip(), settings.smtp_port, timeout=45) as smtp:
                user = (settings.smtp_user or "").strip()
                if user:
                    smtp.login(user, settings.smtp_password or "")
                smtp.send_message(msg)
    except Exception as exc:
        return "", str(exc)[:2000]

    return f"smtp:{uuid.uuid4().hex[:16]}", None
