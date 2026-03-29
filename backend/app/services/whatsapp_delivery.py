"""WhatsApp Cloud API (Meta) text messages. Returns (wamid_or_mock, error_message)."""

from __future__ import annotations

import uuid

import httpx

from app.config import Settings


def send_whatsapp_text(
    *,
    to_digits: str,
    body: str,
    settings: Settings,
) -> tuple[str, str | None]:
    token = (settings.whatsapp_access_token or "").strip()
    phone_id = (settings.whatsapp_phone_number_id or "").strip()
    if not token or not phone_id:
        return f"MOCK-WA-{uuid.uuid4().hex[:12]}", None

    url = f"https://graph.facebook.com/{settings.whatsapp_api_version.strip()}/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_digits,
        "type": "text",
        "text": {"preview_url": False, "body": body[:4096]},
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, headers=headers, json=payload)
            data = r.json()
            if r.status_code >= 400:
                err = data.get("error", {})
                detail = err.get("message", r.text)[:2000]
                return "", detail
            mids = (data.get("messages") or [{}])[0]
            mid = mids.get("id") or f"wa:{uuid.uuid4().hex[:12]}"
            return str(mid), None
    except Exception as exc:
        return "", str(exc)[:2000]
