"""PII minimisation for list/read APIs (not encryption-at-rest — document in security review)."""

import hashlib
import re


def normalize_pan(pan: str) -> str:
    return re.sub(r"\s+", "", pan.strip().upper())


def pan_hash(pan: str) -> str:
    return hashlib.sha256(normalize_pan(pan).encode("utf-8")).hexdigest()


def pan_last_four(pan: str) -> str:
    norm = normalize_pan(pan)
    return norm[-4:] if len(norm) >= 4 else norm


def mask_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) <= 4:
        return "****"
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


def mask_email(email: str) -> str:
    email = email.strip()
    if "@" not in email:
        return "***"
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        return f"***@{domain}"
    return f"{local[:2]}***@{domain}"


def whatsapp_recipient_digits(phone: str) -> str:
    """Meta WhatsApp Cloud API expects digits only, no + (E.164 without plus)."""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("0"):
        digits = digits.lstrip("0")
    if len(digits) == 10:
        digits = "91" + digits
    return digits
