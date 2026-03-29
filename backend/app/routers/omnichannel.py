from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_correlation_id, require_permission
from app.domain.enums import Permission
from app.limiter import limiter
from app.models import OutboundMessage, User
from app.schemas import APISuccessResponse, OmnichannelSendRequest
from app.services.omnichannel_service import send_outbound_message

router = APIRouter(prefix="/omnichannel", tags=["Omnichannel"])


@router.post("/messages", response_model=APISuccessResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def send_message(
    request: Request,
    payload: OmnichannelSendRequest,
    user: User = Depends(require_permission(Permission.OMNICHANNEL_OUTBOUND)),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    row = send_outbound_message(
        db,
        actor=user,
        correlation_id=correlation_id,
        customer_id=payload.customer_id,
        channel=payload.channel,
        subject=payload.subject,
        body=payload.body,
    )
    return APISuccessResponse(
        http_status_code=201,
        message="Outbound message processed",
        result={
            "message_id": row.id,
            "channel": row.channel,
            "status": row.status,
            "destination_masked": row.destination_masked,
            "provider_reference": row.provider_reference,
            "error_message": row.error_message,
            "correlation_id": row.correlation_id,
        },
    )


@router.get("/messages", response_model=APISuccessResponse)
def list_messages(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    channel: str | None = Query(None, description="Filter: whatsapp | email"),
    user: User = Depends(require_permission(Permission.OMNICHANNEL_OUTBOUND)),
    db: Session = Depends(get_db),
):
    base = OutboundMessage.enterprise_id == user.enterprise_id
    if channel in ("whatsapp", "email"):
        base = base & (OutboundMessage.channel == channel)
    elif channel is not None:
        raise HTTPException(status_code=422, detail="channel must be whatsapp, email, or omitted")
    total_count = int(db.execute(select(func.count()).select_from(OutboundMessage).where(base)).scalar_one() or 0)
    q = select(OutboundMessage).where(base).order_by(OutboundMessage.id.desc())
    rows = list(db.execute(q.offset((page - 1) * size).limit(size)).scalars().all())
    items = [
        {
            "id": r.id,
            "customer_id": r.customer_id,
            "channel": r.channel,
            "subject": r.subject,
            "body_preview": (r.body[:200] + "…") if len(r.body) > 200 else r.body,
            "destination_masked": r.destination_masked,
            "status": r.status,
            "provider_reference": r.provider_reference,
            "correlation_id": r.correlation_id,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
    return APISuccessResponse(
        http_status_code=200,
        message="Outbound message history",
        result={"page": page, "size": size, "total": total_count, "items": items},
    )


@router.get("/messages/{message_id}", response_model=APISuccessResponse)
def get_message(
    message_id: int,
    user: User = Depends(require_permission(Permission.OMNICHANNEL_OUTBOUND)),
    db: Session = Depends(get_db),
):
    row = db.get(OutboundMessage, message_id)
    if row is None or row.enterprise_id != user.enterprise_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return APISuccessResponse(
        http_status_code=200,
        message="Outbound message detail",
        result={
            "id": row.id,
            "customer_id": row.customer_id,
            "channel": row.channel,
            "subject": row.subject,
            "body": row.body,
            "destination_masked": row.destination_masked,
            "status": row.status,
            "provider_reference": row.provider_reference,
            "error_message": row.error_message,
            "correlation_id": row.correlation_id,
            "created_at": row.created_at.isoformat(),
        },
    )
