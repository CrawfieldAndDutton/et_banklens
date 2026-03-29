from app.domain.enums import Permission, UserRole

# Analyst: day-to-day monitoring; Compliance: read-only + audit export; Admin: all.
ROLE_DEFAULT_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.ADMIN: frozenset(Permission),
    UserRole.ANALYST: frozenset(
        {
            Permission.CUSTOMER_CREATION,
            Permission.CUSTOMER_MODIFICATION,
            Permission.TRIGGER_BSI_PROCESS,
            Permission.REVIEW_BSI_REPORT,
            Permission.OMNICHANNEL_OUTBOUND,
        }
    ),
    UserRole.COMPLIANCE: frozenset(
        {
            Permission.REVIEW_BSI_REPORT,
            Permission.AUDIT_AI_AGENT_CALL_REPORT,
        }
    ),
}


def effective_permissions(role: UserRole, extra_json: list[str] | None) -> frozenset[Permission]:
    base = ROLE_DEFAULT_PERMISSIONS[role]
    if not extra_json:
        return base
    extra: set[Permission] = set()
    for p in extra_json:
        try:
            extra.add(Permission(p))
        except ValueError:
            continue
    return frozenset(base | extra)
