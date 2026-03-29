from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Enterprise(Base):
    __tablename__ = "enterprises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="enterprise")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("enterprises.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="analyst")
    permissions_extra_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    enterprise: Mapped[Enterprise] = relationship(back_populates="users")


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("enterprise_id", "pan_hash", name="uq_customer_enterprise_pan"),
        UniqueConstraint("enterprise_id", "external_ref", name="uq_customer_enterprise_ref"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("enterprises.id"), index=True, nullable=False)
    external_ref: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    pan_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    pan_last_four: Mapped[str] = mapped_column(String(4), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    loan_type: Mapped[str] = mapped_column(String(64), nullable=False)
    consent_monitoring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    enterprise: Mapped[Enterprise] = relationship()
    loan: Mapped[LoanAccount | None] = relationship(back_populates="customer", uselist=False)


class LoanAccount(Base):
    __tablename__ = "loan_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), unique=True, nullable=False, index=True)
    principal_outstanding: Mapped[int] = mapped_column(Integer, nullable=False)
    emi_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    dpd_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_monthly_inflow: Mapped[int] = mapped_column(Integer, nullable=False)
    eod_negative_days_90d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    credit_score_delta_90d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    salary_proxy_delta_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer: Mapped[Customer] = relationship(back_populates="loan")


class BSIMonitoringRun(Base):
    __tablename__ = "bsi_monitoring_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("enterprises.id"), index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    triggered_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    input_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    gen_ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    gen_ai_model: Mapped[str | None] = mapped_column(String(128), nullable=True)

    signals: Mapped[list[Signal]] = relationship(back_populates="run")


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("bsi_monitoring_runs.id"), index=True, nullable=False)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("enterprises.id"), index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    narrative: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    run: Mapped[BSIMonitoringRun] = relationship(back_populates="signals")


class OutboundMessage(Base):
    """WhatsApp / email outbound attempt (omnichannel slice)."""

    __tablename__ = "outbound_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("enterprises.id"), index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(300), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    destination_masked: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    triggered_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditEvent(Base):
    """Append-only compliance log; every guardrail and agent step should emit rows."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("enterprises.id"), index=True, nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_code: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_pack_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    inputs_redacted_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    outcome_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
