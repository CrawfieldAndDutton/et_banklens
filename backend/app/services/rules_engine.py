"""
Deterministic monitoring rules (Bank Statement Intelligence stand-in).

Every rule emits a structured evaluation record for audit (`AGENT_RULE_EVALUATED`).
No external LLM: reviewers can replay decisions from version + inputs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.domain.enums import BSISignalType, CustomerRiskLevel, DPDBucket, SignalSeverity


@dataclass(frozen=True)
class RuleEvaluation:
    rule_id: str
    matched: bool
    signal_type: BSISignalType | None
    severity: SignalSeverity | None
    narrative: str | None
    inputs_used: dict[str, Any]


def _severity_for_dpd(dpd_days: int) -> SignalSeverity:
    if dpd_days >= 60:
        return SignalSeverity.HIGH
    if dpd_days >= 30:
        return SignalSeverity.MEDIUM
    return SignalSeverity.LOW


def classify_dpd_bucket(dpd_days: int, avg_monthly_inflow: int, emi_amount: int) -> DPDBucket:
    """Stress-aware bucket: thin liquidity accelerates outlook."""
    if dpd_days <= 0 and emi_amount <= max(avg_monthly_inflow, 1) * 0.45:
        return DPDBucket.NOT_LIKELY
    if dpd_days >= 60 or (dpd_days >= 30 and emi_amount > avg_monthly_inflow):
        return DPDBucket.BUCKET_60_90
    if dpd_days >= 30:
        return DPDBucket.BUCKET_30_60
    if dpd_days >= 15:
        return DPDBucket.BUCKET_15_30
    if dpd_days > 0:
        return DPDBucket.BUCKET_0_15
    if emi_amount > avg_monthly_inflow:
        return DPDBucket.BUCKET_0_15
    return DPDBucket.NOT_LIKELY


def aggregate_risk(levels: list[SignalSeverity]) -> CustomerRiskLevel:
    if any(s == SignalSeverity.HIGH for s in levels):
        return CustomerRiskLevel.HIGH
    if any(s == SignalSeverity.MEDIUM for s in levels):
        return CustomerRiskLevel.MEDIUM
    return CustomerRiskLevel.LOW


def evaluate_rules(
    *,
    rule_pack_version: str,
    customer_ref: str,
    dpd_days: int,
    emi_amount: int,
    avg_monthly_inflow: int,
    eod_negative_days_90d: int,
    credit_score_delta_90d: int,
    salary_proxy_delta_pct: int,
) -> tuple[list[RuleEvaluation], CustomerRiskLevel, DPDBucket]:
    emi_ratio_pct = round(100 * emi_amount / max(avg_monthly_inflow, 1))

    evaluations: list[RuleEvaluation] = []

    # R_DPD_LATE — delinquency ladder
    matched_dpd = dpd_days > 0
    evaluations.append(
        RuleEvaluation(
            rule_id="R_DPD_LATE",
            matched=matched_dpd,
            signal_type=BSISignalType.LATE_PAYMENT if matched_dpd else None,
            severity=_severity_for_dpd(dpd_days) if matched_dpd else None,
            narrative=(
                f"DPD={dpd_days} days exceeds 0; classify delinquency severity per ladder."
                if matched_dpd
                else "No material delinquency on snapshot."
            ),
            inputs_used={"dpd_days": dpd_days, "rule_pack_version": rule_pack_version, "customer_ref": customer_ref},
        )
    )

    # R_BOUNCE_PROXY — insufficient funds / negative balance pattern (proxy, not cheque imaging)
    matched_bounce = eod_negative_days_90d >= 5
    evaluations.append(
        RuleEvaluation(
            rule_id="R_BOUNCE_PROXY",
            matched=matched_bounce,
            signal_type=BSISignalType.BOUNCE_DETECTED if matched_bounce else None,
            severity=(
                (SignalSeverity.HIGH if eod_negative_days_90d >= 15 else SignalSeverity.MEDIUM)
                if matched_bounce
                else None
            ),
            narrative=(
                f"Negative EOD pattern on {eod_negative_days_90d} / 90 days (proxy for bounce/liquidity stress)."
                if matched_bounce
                else "Negative EOD count below bounce proxy threshold."
            ),
            inputs_used={
                "eod_negative_days_90d": eod_negative_days_90d,
                "threshold_soft": 5,
                "threshold_hard": 15,
            },
        )
    )

    # R_NEG_EOD — sustained negative closing balance
    matched_ne = eod_negative_days_90d >= 10
    evaluations.append(
        RuleEvaluation(
            rule_id="R_NEG_EOD",
            matched=matched_ne,
            signal_type=BSISignalType.NEGATIVE_EOD_BALANCE if matched_ne else None,
            severity=SignalSeverity.HIGH if matched_ne else None,
            narrative=(
                "Sustained negative end-of-day balances indicate liquidity strain."
                if matched_ne
                else "Negative EOD below sustained threshold."
            ),
            inputs_used={"eod_negative_days_90d": eod_negative_days_90d, "threshold": 10},
        )
    )

    # R_CREDIT — bureau delta (synthetic field in demo dataset)
    matched_cr = credit_score_delta_90d <= -20
    evaluations.append(
        RuleEvaluation(
            rule_id="R_CREDIT",
            matched=matched_cr,
            signal_type=BSISignalType.CREDIT_SCORE_DROP if matched_cr else None,
            severity=SignalSeverity.MEDIUM if matched_cr else None,
            narrative=(
                f"Bureau score delta {credit_score_delta_90d} points over 90d breaches threshold -20."
                if matched_cr
                else "Bureau delta within tolerance."
            ),
            inputs_used={"credit_score_delta_90d": credit_score_delta_90d, "threshold": -20},
        )
    )

    # R_EMI_LOAD — commitment ratio
    matched_emi = emi_ratio_pct >= 50
    evaluations.append(
        RuleEvaluation(
            rule_id="R_EMI_LOAD",
            matched=matched_emi,
            signal_type=BSISignalType.HIGHER_EMI_LOAD if matched_emi else None,
            severity=SignalSeverity.HIGH if emi_ratio_pct >= 65 else SignalSeverity.MEDIUM,
            narrative=(
                f"EMI to inflow ratio {emi_ratio_pct}% exceeds policy 50%."
                if matched_emi
                else f"EMI to inflow ratio {emi_ratio_pct}% within policy."
            ),
            inputs_used={
                "emi_amount": emi_amount,
                "avg_monthly_inflow": avg_monthly_inflow,
                "emi_ratio_pct": emi_ratio_pct,
                "threshold_pct": 50,
            },
        )
    )

    # R_SALARY — income proxy deterioration
    matched_sal = salary_proxy_delta_pct <= -15
    evaluations.append(
        RuleEvaluation(
            rule_id="R_SALARY",
            matched=matched_sal,
            signal_type=BSISignalType.SALARY_DROP if matched_sal else None,
            severity=SignalSeverity.MEDIUM if matched_sal else None,
            narrative=(
                f"Income proxy down {abs(salary_proxy_delta_pct)}% vs baseline (threshold 15%)."
                if matched_sal
                else "Income proxy stable vs baseline."
            ),
            inputs_used={"salary_proxy_delta_pct": salary_proxy_delta_pct, "threshold_pct": -15},
        )
    )

    severities = [e.severity for e in evaluations if e.matched and e.severity is not None]
    risk = aggregate_risk(severities) if severities else CustomerRiskLevel.LOW
    bucket = classify_dpd_bucket(dpd_days, avg_monthly_inflow, emi_amount)

    return evaluations, risk, bucket


def redacted_feature_snapshot(
    *,
    customer_external_ref: str,
    loan: dict[str, int],
    rule_pack_version: str,
) -> str:
    payload = {
        "customer_external_ref": customer_external_ref,
        "rule_pack_version": rule_pack_version,
        "features": {
            "dpd_days": loan["dpd_days"],
            "emi_amount": loan["emi_amount"],
            "avg_monthly_inflow": loan["avg_monthly_inflow"],
            "eod_negative_days_90d": loan["eod_negative_days_90d"],
            "credit_score_delta_90d": loan["credit_score_delta_90d"],
            "salary_proxy_delta_pct": loan["salary_proxy_delta_pct"],
        },
        "pii_note": "PAN/phone/email excluded by policy from BSI snapshots.",
    }
    return json.dumps(payload, sort_keys=True)
