from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.domain.enums import LoanType, OmnichannelChannel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    enterprise_slug: str = Field(default="demo", max_length=64)


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    enterprise_id: int
    role: str

    model_config = {"from_attributes": True}


class APISuccessResponse(BaseModel):
    """Aligned with Minerva `dto.common_dto.APISuccessResponse` for familiar clients."""

    http_status_code: int | None = None
    message: str | None = None
    result: Any | None = None

    model_config = {"exclude_none": True}


class LoanSnapshotIn(BaseModel):
    principal_outstanding: int = Field(ge=0, le=10_000_000_000)
    emi_amount: int = Field(ge=0, le=10_000_000)
    dpd_days: int = Field(ge=0, le=3650)
    avg_monthly_inflow: int = Field(ge=1, le=10_000_000)
    eod_negative_days_90d: int = Field(ge=0, le=90)
    credit_score_delta_90d: int = Field(ge=-900, le=900)
    salary_proxy_delta_pct: int = Field(ge=-100, le=500)


class CustomerCreateRequest(BaseModel):
    external_ref: str = Field(min_length=1, max_length=64)
    display_name: str = Field(min_length=1, max_length=255)
    pan: str = Field(min_length=10, max_length=10)
    phone: str = Field(min_length=10, max_length=20)
    email: EmailStr | None = None
    loan_type: LoanType
    consent_monitoring: bool = False
    loan_snapshot: LoanSnapshotIn | None = None

    @field_validator("pan")
    @classmethod
    def pan_alnum(cls, v: str) -> str:
        p = v.strip().upper()
        if not p.isalnum() or len(p) != 10:
            raise ValueError("PAN must be 10 alphanumeric characters")
        return p

    @model_validator(mode="after")
    def strip_core_fields(self):
        self.display_name = self.display_name.strip()
        self.external_ref = self.external_ref.strip()
        self.phone = self.phone.strip()
        return self


class CustomerCreatedResponse(BaseModel):
    id: int
    external_ref: str
    pan_last4: str
    phone_masked: str
    consent_monitoring: bool
    loan_type: str


class MonitoredCustomerRow(BaseModel):
    customer_id: int
    external_ref: str
    display_name: str
    phone_masked: str
    pan_last4: str
    loan_type: str
    consent_monitoring: bool
    last_bsi_status: str | None
    has_loan_snapshot: bool


class ConsentUpdateRequest(BaseModel):
    consent_monitoring: bool


class OmnichannelSendRequest(BaseModel):
    customer_id: int = Field(ge=1)
    channel: OmnichannelChannel
    subject: str | None = Field(None, max_length=240)
    body: str = Field(..., min_length=1, max_length=16000)

    @model_validator(mode="after")
    def channel_rules(self):
        if self.channel == OmnichannelChannel.WHATSAPP:
            if len(self.body) > 4096:
                raise ValueError("WhatsApp body must be at most 4096 characters")
            if self.subject is not None and self.subject.strip() != "":
                raise ValueError("subject must be omitted for WhatsApp")
        if self.channel == OmnichannelChannel.EMAIL:
            if not (self.subject or "").strip():
                raise ValueError("subject is required for the email channel")
        return self
