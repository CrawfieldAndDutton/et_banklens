"""Dashboard aggregates (Minerva `DashboardHandler` analogue, SQL-only)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enums import BSIStatus
from app.models import BSIMonitoringRun, Customer, LoanAccount, Signal


def get_dashboard_statistics(
    db: Session,
    *,
    enterprise_id: int,
    year: int | None,
    month: int | None,
    loan_type: str | None,
) -> dict[str, Any]:
    cust_q = select(Customer).where(Customer.enterprise_id == enterprise_id)
    if loan_type:
        cust_q = cust_q.where(Customer.loan_type == loan_type)
    if year is not None:
        cust_q = cust_q.where(func.strftime("%Y", Customer.created_at) == str(year))
    if month is not None:
        if month < 1 or month > 12:
            raise ValueError("month must be 1–12")
        cust_q = cust_q.where(func.strftime("%m", Customer.created_at) == str(month).zfill(2))

    customers = list(db.execute(cust_q).scalars().all())
    total_customers = len(customers)
    if total_customers == 0:
        return {
            "total_customers": 0,
            "customers_with_monitoring_consent": 0,
            "customers_with_loan_snapshot": 0,
            "risky_customers_signal_based": 0,
            "total_compiled_signals": 0,
            "signals_by_severity": {},
            "completed_bsi_runs_last_30_days": 0,
            "filters_applied": {"year": year, "month": month, "loan_type": loan_type},
            "recovery_rate": 0.0,
            "note": "No customers match the current filters.",
        }
    consenting = sum(1 for c in customers if c.consent_monitoring)

    sig_base = select(Signal).where(Signal.enterprise_id == enterprise_id)
    if customers:
        ids = [c.id for c in customers]
        sig_base = sig_base.where(Signal.customer_id.in_(ids))
    signals = list(db.execute(sig_base).scalars().all())
    by_sev: dict[str, int] = defaultdict(int)
    for s in signals:
        by_sev[s.severity] += 1

    risky_customers = len({s.customer_id for s in signals if s.severity in ("HIGH", "MEDIUM")})

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=30)
    runs_q = select(func.count()).select_from(BSIMonitoringRun).where(
        BSIMonitoringRun.enterprise_id == enterprise_id,
        BSIMonitoringRun.status == BSIStatus.COMPLETED.value,
        BSIMonitoringRun.completed_at.is_not(None),
        BSIMonitoringRun.completed_at >= since,
    )
    runs_30d = int(db.execute(runs_q).scalar_one() or 0)

    loan_count = 0
    if customers:
        loan_count = int(
            db.execute(
                select(func.count())
                .select_from(LoanAccount)
                .where(LoanAccount.customer_id.in_([c.id for c in customers]))
            ).scalar_one()
            or 0
        )

    return {
        "total_customers": total_customers,
        "customers_with_monitoring_consent": consenting,
        "customers_with_loan_snapshot": loan_count,
        "risky_customers_signal_based": risky_customers,
        "total_compiled_signals": len(signals),
        "signals_by_severity": dict(by_sev),
        "completed_bsi_runs_last_30_days": runs_30d,
        "filters_applied": {
            "year": year,
            "month": month,
            "loan_type": loan_type,
        },
        "recovery_rate": 0.0,
        "note": "Recovery rate placeholder (not modelled in this slice).",
    }


def latest_signals(
    db: Session,
    *,
    enterprise_id: int,
    limit: int = 5,
) -> list[dict[str, Any]]:
    rows = list(
        db.execute(
            select(Signal)
            .where(Signal.enterprise_id == enterprise_id)
            .order_by(Signal.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [
        {
            "signal_id": r.id,
            "customer_id": r.customer_id,
            "signal_type": r.signal_type,
            "severity": r.severity,
            "narrative": r.narrative,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
