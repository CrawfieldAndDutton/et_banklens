"""Idempotent demo data: enterprise, roles, borrowers, loan snapshots."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.config import Settings, get_settings
from app.database import SessionLocal
from app.domain.enums import UserRole
from app.models import Customer, Enterprise, LoanAccount, User
from app.security import hash_password
from app.services.pii import pan_hash, pan_last_four

logger = logging.getLogger("banklens")


def _ensure_enterprise(session, slug: str, name: str) -> Enterprise:
    row = session.execute(select(Enterprise).where(Enterprise.slug == slug)).scalar_one_or_none()
    if row:
        return row
    ent = Enterprise(slug=slug, name=name)
    session.add(ent)
    session.commit()
    session.refresh(ent)
    return ent


def run_seed(settings: Settings) -> None:
    with SessionLocal() as session:
        ent = _ensure_enterprise(session, settings.default_enterprise_slug, "Demo NBFC (BankLens)")

        if settings.seed_demo_user and settings.demo_user_password:
            email = settings.demo_user_email
            user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if user is None:
                session.add(
                    User(
                        email=email,
                        hashed_password=hash_password(settings.demo_user_password),
                        is_active=True,
                        enterprise_id=ent.id,
                        role=UserRole.ADMIN.value,
                        permissions_extra_json="[]",
                    )
                )
                session.commit()
                logger.info("Seeded demo admin user")
            else:
                changed = False
                if user.enterprise_id != ent.id:
                    user.enterprise_id = ent.id
                    changed = True
                if user.role != UserRole.ADMIN.value:
                    user.role = UserRole.ADMIN.value
                    changed = True
                if changed:
                    session.commit()
                    logger.info("Updated demo user enterprise/role")

        if not settings.seed_banklens_demo:
            return

        def add_customer(
            *,
            ref: str,
            name: str,
            pan: str,
            phone: str,
            email: str | None = None,
            loan_type: str,
            consent: bool,
            loan: dict | None,
        ) -> None:
            ph = pan_hash(pan)
            exists = session.execute(
                select(Customer).where(Customer.enterprise_id == ent.id, Customer.pan_hash == ph)
            ).scalar_one_or_none()
            if exists:
                return
            c = Customer(
                enterprise_id=ent.id,
                external_ref=ref,
                display_name=name,
                pan_hash=ph,
                pan_last_four=pan_last_four(pan),
                phone=phone,
                email=email,
                loan_type=loan_type,
                consent_monitoring=consent,
                consent_recorded_at=datetime.now(timezone.utc) if consent else None,
            )
            session.add(c)
            session.commit()
            session.refresh(c)
            if loan:
                session.add(
                    LoanAccount(
                        customer_id=c.id,
                        principal_outstanding=loan["principal_outstanding"],
                        emi_amount=loan["emi_amount"],
                        dpd_days=loan["dpd_days"],
                        avg_monthly_inflow=loan["avg_monthly_inflow"],
                        eod_negative_days_90d=loan["eod_negative_days_90d"],
                        credit_score_delta_90d=loan["credit_score_delta_90d"],
                        salary_proxy_delta_pct=loan["salary_proxy_delta_pct"],
                    )
                )
                session.commit()

        # Stressed retail borrower — expect multiple signals when BSI runs
        add_customer(
            ref="CUST-1001",
            name="Aditi Sharma",
            pan="ABCDE1234F",
            phone="+919876543210",
            loan_type="Personal Loan",
            consent=True,
            loan={
                "principal_outstanding": 420000,
                "emi_amount": 18500,
                "dpd_days": 22,
                "avg_monthly_inflow": 28000,
                "eod_negative_days_90d": 12,
                "credit_score_delta_90d": -35,
                "salary_proxy_delta_pct": -22,
            },
        )
        # Healthy borrower — mostly clear rules
        add_customer(
            ref="CUST-1002",
            name="Rahul Verma",
            pan="FGHIJ5678K",
            phone="+919811122233",
            email="rahul.verma@example.com",
            loan_type="Home Loan",
            consent=True,
            loan={
                "principal_outstanding": 3500000,
                "emi_amount": 32000,
                "dpd_days": 0,
                "avg_monthly_inflow": 95000,
                "eod_negative_days_90d": 1,
                "credit_score_delta_90d": -5,
                "salary_proxy_delta_pct": 2,
            },
        )
        # Consent withheld — guardrail demonstrations
        add_customer(
            ref="CUST-1003",
            name="Casey NoConsent",
            pan="LMNOP9012Q",
            phone="+919000000003",
            loan_type="Business Loan",
            consent=False,
            loan={
                "principal_outstanding": 800000,
                "emi_amount": 22000,
                "dpd_days": 5,
                "avg_monthly_inflow": 40000,
                "eod_negative_days_90d": 6,
                "credit_score_delta_90d": -10,
                "salary_proxy_delta_pct": -5,
            },
        )

        # Optional role-separated accounts for reviewer walkthroughs
        for email, role, pwd in (
            ("analyst@example.com", UserRole.ANALYST.value, settings.demo_user_password),
            ("compliance@example.com", UserRole.COMPLIANCE.value, settings.demo_user_password),
        ):
            if not pwd:
                continue
            if session.execute(select(User).where(User.email == email)).scalar_one_or_none():
                continue
            session.add(
                User(
                    email=email,
                    hashed_password=hash_password(pwd),
                    is_active=True,
                    enterprise_id=ent.id,
                    role=role,
                    permissions_extra_json=json.dumps([]),
                )
            )
            session.commit()
            logger.info("Seeded role user %s", email)
