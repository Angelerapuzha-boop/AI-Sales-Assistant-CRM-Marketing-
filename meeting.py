import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.google_calendar import calendar_service
from app.integrations.telegram import telegram_service
from app.models import Company, Contact, Meeting, MeetingStatus, User, UserRole
from app.schemas import MeetingCreate, MeetingResponse, MeetingUpdate, PaginatedResponse
from app.services.ai_service import ai_service
from app.services.notification_service import notify_meeting_scheduled
from app.utils.security import get_current_user

router = APIRouter(prefix="/meetings", tags=["Meetings"])


def _meeting_query(db: Session, user: User):
    q = db.query(Meeting)
    if user.role != UserRole.ADMIN:
        q = q.filter(Meeting.organizer_id == user.id)
    return q


@router.get("", response_model=PaginatedResponse)
def list_meetings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: MeetingStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _meeting_query(db, current_user)
    if status:
        query = query.filter(Meeting.status == status)
    total = query.count()
    items = query.order_by(Meeting.start_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[MeetingResponse.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=MeetingResponse, status_code=201)
async def create_meeting(
    data: MeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = Meeting(organizer_id=current_user.id, **data.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    if current_user.google_tokens:
        contact = db.query(Contact).filter(Contact.id == data.contact_id).first() if data.contact_id else None
        attendees = [contact.email] if contact and contact.email else None
        result = calendar_service.create_event(
            current_user.google_tokens,
            meeting.title,
            meeting.start_time,
            meeting.end_time,
            meeting.description,
            attendees,
            meeting.location,
        )
        if result.get("success"):
            meeting.google_event_id = result.get("event_id")
            meeting.meeting_link = result.get("link")
            db.commit()
            db.refresh(meeting)

    notify_meeting_scheduled(db, current_user.id, meeting.title, meeting.start_time.isoformat())
    await telegram_service.notify_meeting_scheduled(meeting.title, meeting.start_time.isoformat())
    return MeetingResponse.model_validate(meeting)


@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = _meeting_query(db, current_user).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingResponse.model_validate(meeting)


@router.put("/{meeting_id}", response_model=MeetingResponse)
def update_meeting(
    meeting_id: UUID,
    data: MeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = _meeting_query(db, current_user).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(meeting, field, value)
    if meeting.google_event_id and current_user.google_tokens:
        calendar_service.update_event(current_user.google_tokens, meeting.google_event_id, {"summary": meeting.title})
    db.commit()
    db.refresh(meeting)
    return MeetingResponse.model_validate(meeting)


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(
    meeting_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = _meeting_query(db, current_user).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.google_event_id and current_user.google_tokens:
        calendar_service.delete_event(current_user.google_tokens, meeting.google_event_id)
    db.delete(meeting)
    db.commit()


@router.post("/{meeting_id}/prep-notes")
def generate_prep_notes(
    meeting_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = _meeting_query(db, current_user).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    company = db.query(Company).filter(Company.id == meeting.company_id).first() if meeting.company_id else None
    company_data = {"name": company.name, "industry": company.industry} if company else {}
    notes, provider = ai_service.generate_meeting_prep(
        {"title": meeting.title, "start": str(meeting.start_time)},
        company_data,
    )
    meeting.prep_notes = notes
    db.commit()
    return {"prep_notes": notes, "provider": provider}
