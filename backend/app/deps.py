from __future__ import annotations

import json
import uuid

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import AuditEventType, Permission, UserRole
from app.domain.permissions import effective_permissions
from app.models import User
from app.security import decode_token
from app.services import audit_service

bearer_scheme = HTTPBearer(auto_error=False)


def get_correlation_id(x_correlation_id: str | None = Header(None, alias="X-Correlation-ID")) -> str:
    cid = (x_correlation_id or "").strip()
    if cid and len(cid) <= 128:
        return cid
    return str(uuid.uuid4())


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = decode_token(credentials.credentials)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_permission(perm: Permission):
    def _checker(
        user: User = Depends(get_current_user),
        correlation_id: str = Depends(get_correlation_id),
    ) -> User:
        try:
            role = UserRole(user.role)
        except ValueError:
            role = UserRole.ANALYST
        raw = json.loads(user.permissions_extra_json or "[]")
        extra_list = [str(x) for x in raw] if isinstance(raw, list) else []
        allowed = effective_permissions(role, extra_list)
        if perm not in allowed:
            audit_service.record_audit(
                enterprise_id=user.enterprise_id,
                actor_user_id=user.id,
                correlation_id=correlation_id,
                event_type=AuditEventType.PERMISSION_DENIED,
                resource_type="api",
                resource_id=perm.value,
                decision_code="RBAC_DENIED",
                rule_pack_version=None,
                inputs_redacted={"required_permission": perm.value, "role": user.role},
                outcome={"allowed": False},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission not granted for this action.",
            )
        return user

    return _checker
