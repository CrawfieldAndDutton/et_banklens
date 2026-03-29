from enum import Enum


class UserRole(str, Enum):
    """Coarse roles; fine-grained checks use Permission."""

    ADMIN = "admin"
    ANALYST = "analyst"
    COMPLIANCE = "compliance"


class Permission(str, Enum):
    """Subset aligned with Minerva `PermissionChoices` for reviewer familiarity."""

    CUSTOMER_CREATION = "CustomerCreation"
    CUSTOMER_MODIFICATION = "CustomerModification"
    TRIGGER_BSI_PROCESS = "TriggerBSIProcess"
    REVIEW_BSI_REPORT = "ReviewBSIReport"
    AUDIT_AI_AGENT_CALL_REPORT = "AuditAIAgentCallReport"
    OMNICHANNEL_OUTBOUND = "OmnichannelOutbound"


class BSIStatus(str, Enum):
    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SignalSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class BSISignalType(str, Enum):
    """Representative bank / credit signals (subset of Minerva `BSISignals`)."""

    BOUNCE_DETECTED = "BOUNCE_DETECTED"
    NEGATIVE_EOD_BALANCE = "NEGATIVE_EOD_BALANCE"
    LATE_PAYMENT = "LATE_PAYMENT"
    CREDIT_SCORE_DROP = "CREDIT_SCORE_DROP"
    HIGHER_EMI_LOAD = "HIGHER_EMI_LOAD"
    SALARY_DROP = "SALARY_DROP"


class LoanType(str, Enum):
    PERSONAL = "Personal Loan"
    HOME = "Home Loan"
    BUSINESS = "Business Loan"
    EDUCATION = "Education Loan"


class CustomerRiskLevel(str, Enum):
    LOW = "LOW_RISK"
    MEDIUM = "MEDIUM_RISK"
    HIGH = "HIGH_RISK"


class DPDBucket(str, Enum):
    """Human-readable DPD outlook bands (see Minerva `DPDOccurrenceConstants`)."""

    BUCKET_0_15 = "Likely within 0–15 days"
    BUCKET_15_30 = "Likely within 15–30 days"
    BUCKET_30_60 = "Likely within 30–60 days"
    BUCKET_60_90 = "Likely within 60–90 days"
    NOT_LIKELY = "Not Likely"


class AuditEventType(str, Enum):
    DATA_ACCESSED = "DATA_ACCESSED"
    CONSENT_RECORD_UPDATED = "CONSENT_RECORD_UPDATED"
    CUSTOMER_CREATED = "CUSTOMER_CREATED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    GUARDRAIL_BLOCKED = "GUARDRAIL_BLOCKED"
    BSI_TRIGGER_REQUESTED = "BSI_TRIGGER_REQUESTED"
    BSI_RUN_STATE_CHANGED = "BSI_RUN_STATE_CHANGED"
    AGENT_RULE_EVALUATED = "AGENT_RULE_EVALUATED"
    AGENT_DECISION_FINAL = "AGENT_DECISION_FINAL"
    GEN_AI_INVOKED = "GEN_AI_INVOKED"
    GEN_AI_COMPLETED = "GEN_AI_COMPLETED"
    GEN_AI_SKIPPED = "GEN_AI_SKIPPED"
    GEN_AI_FAILED = "GEN_AI_FAILED"
    OMNICHANNEL_OUTBOUND_REQUESTED = "OMNICHANNEL_OUTBOUND_REQUESTED"
    OMNICHANNEL_OUTBOUND_RESULT = "OMNICHANNEL_OUTBOUND_RESULT"


class OmnichannelChannel(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class OutboundDeliveryStatus(str, Enum):
    SENT = "SENT"
    FAILED = "FAILED"
    MOCKED = "MOCKED"


class RetentionClass(str, Enum):
    """Data minimisation / retention labelling for audit reviewers."""

    OPERATIONAL = "OPERATIONAL"
    AUDIT_IMMUTABLE = "AUDIT_IMMUTABLE"
