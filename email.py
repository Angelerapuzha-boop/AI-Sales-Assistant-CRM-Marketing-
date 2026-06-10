import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.gmail import gmail_service
from app.integrations.telegram import telegram_service
from app.models import Company, Contact, Email, EmailEvent, EmailStatus, User, UserRole
from app.schemas import EmailCreate, EmailGenerateRequest, EmailResponse, PaginatedResponse
from app.services.ai_service import ai_service
from app.services.notification_service import notify_email_sent
from app.utils.security import get_current_user

router = APIRouter(prefix="/emails", tags=["Emails"])


def _email_query(db: Session, user: User):
    q = db.query(Email)
    if user.role != UserRole.ADMIN:
        q = q.filter(Email.sender_id == user.id)
    return q


@router.get("", response_model=PaginatedResponse)
def list_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: EmailStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _email_query(db, current_user)
    if status:
        query = query.filter(Email.status == status)
    total = query.count()
    items = query.order_by(Email.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[EmailResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("/generate")
def generate_email(
    data: EmailGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    contact = db.query(Contact).filter(Contact.id == data.contact_id).first() if data.contact_id else None
    contact_name = f"{contact.first_name} {contact.last_name}" if contact else "there"
    content, provider = ai_service.generate_email(
        data.email_type,
        company.name,
        contact_name,
        company.industry or "",
        current_user.full_name,
        data.context or "",
    )
    lines = content.strip().split("\n", 1)
    subject = lines[0].replace("Subject:", "").strip() if lines else f"Re: {company.name}"
    body = lines[1].strip() if len(lines) > 1 else content
    return {"subject": subject, "body": body, "provider": provider}


@router.post("", response_model=EmailResponse, status_code=201)
def create_email(
    data: EmailCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    email = Email(sender_id=current_user.id, **data.model_dump())
    db.add(email)
    db.commit()
    db.refresh(email)
    return EmailResponse.model_validate(email)


@router.post("/{email_id}/send", response_model=EmailResponse)
async def send_email(
    email_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    email = _email_query(db, current_user).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    contact = db.query(Contact).filter(Contact.id == email.contact_id).first() if email.contact_id else None
    to_address = contact.email if contact and contact.email else None

    if current_user.gmail_tokens and to_address:
        result = gmail_service.send_email(
            current_user.gmail_tokens,
            to_address,
            email.subject,
            email.body,
            current_user.email,
        )
        if result.get("success"):
            email.status = EmailStatus.SENT
            email.sent_at = datetime.now(timezone.utc)
            email.gmail_message_id = result.get("message_id")
            email.thread_id = result.get("thread_id")
            db.add(EmailEvent(email_id=email.id, event_type="sent", metadata_={"gmail_id": result.get("message_id")}))
        else:
            email.status = EmailStatus.FAILED
            db.add(EmailEvent(email_id=email.id, event_type="failed", metadata_=result))
    else:
        email.status = EmailStatus.SENT
        email.sent_at = datetime.now(timezone.utc)
        db.add(EmailEvent(email_id=email.id, event_type="sent", metadata_={"mode": "local"}))

    db.commit()
    db.refresh(email)
    notify_email_sent(db, current_user.id, email.subject)
    await telegram_service.notify_email_sent(email.subject)
    return EmailResponse.model_validate(email)


@router.get("/analytics/summary")
def email_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    emails = _email_query(db, current_user).all()
    sent = [e for e in emails if e.status == EmailStatus.SENT]
    return {
        "total": len(emails),
        "sent": len(sent),
        "drafts": len([e for e in emails if e.status == EmailStatus.DRAFT]),
        "failed": len([e for e in emails if e.status == EmailStatus.FAILED]),
        "open_rate": round(len([e for e in sent if e.opened_at]) / len(sent) * 100, 1) if sent else 0,
        "reply_rate": round(len([e for e in sent if e.replied_at]) / len(sent) * 100, 1) if sent else 0,
    }
