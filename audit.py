from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuditLog


def log_audit(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: str | UUID | None = None,
    user_id: UUID | None = None,
    details: dict | None = None,
    request: Request | None = None,
) -> None:
    ip = None
    if request and request.client:
        ip = request.client.host
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        details=details,
        ip_address=ip,
    )
    db.add(entry)
    db.commit()
