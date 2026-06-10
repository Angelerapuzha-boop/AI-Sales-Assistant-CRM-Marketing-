import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.bland_ai import bland_ai_service
from app.models import CallLog, CallStatus, Company, Contact, User, UserRole
from app.schemas import CallCreate, CallResponse, PaginatedResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/calls", tags=["Calls"])


@router.get("", response_model=PaginatedResponse)
def list_calls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(CallLog)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(CallLog.user_id == current_user.id)
    total = query.count()
    items = query.order_by(CallLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[CallResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=CallResponse, status_code=201)
async def initiate_call(
    data: CallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == data.company_id).first() if data.company_id else None
    contact = db.query(Contact).filter(Contact.id == data.contact_id).first() if data.contact_id else None

    task = f"""You are a professional sales representative conducting a lead qualification call.
Company: {company.name if company else 'Unknown'}
Contact: {contact.first_name if contact else 'Prospect'} {contact.last_name if contact else ''}
Goal: Qualify the lead, understand their needs, and determine if they're a good fit.
Be professional, friendly, and concise."""

    call_log = CallLog(
        user_id=current_user.id,
        company_id=data.company_id,
        contact_id=data.contact_id,
        phone_number=data.phone_number,
        status=CallStatus.PENDING,
        scheduled_at=data.scheduled_at,
    )
    db.add(call_log)
    db.commit()
    db.refresh(call_log)

    if data.scheduled_at:
        result = await bland_ai_service.schedule_call(data.phone_number, task, data.scheduled_at.isoformat())
    else:
        result = await bland_ai_service.initiate_call(data.phone_number, task)

    if result.get("success"):
        call_log.bland_call_id = result.get("call_id")
        call_log.status = CallStatus.IN_PROGRESS
    else:
        call_log.status = CallStatus.FAILED
        call_log.summary = f"Call failed: {result.get('error', 'Unknown error')}"

    db.commit()
    db.refresh(call_log)
    return CallResponse.model_validate(call_log)


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(call_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    call = db.query(CallLog).filter(CallLog.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    if current_user.role != UserRole.ADMIN and call.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if call.bland_call_id and call.status == CallStatus.IN_PROGRESS:
        details = await bland_ai_service.get_call_details(call.bland_call_id)
        if details.get("success"):
            data = details.get("data", {})
            call.transcript = data.get("transcript") or call.transcript
            call.summary = data.get("summary") or call.summary
            call.duration_seconds = data.get("call_length") or call.duration_seconds
            if data.get("status") == "completed":
                call.status = CallStatus.COMPLETED
            db.commit()
            db.refresh(call)

    return CallResponse.model_validate(call)


@router.get("/analytics/summary")
def call_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(CallLog)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(CallLog.user_id == current_user.id)
    calls = query.all()
    return {
        "total": len(calls),
        "completed": len([c for c in calls if c.status == CallStatus.COMPLETED]),
        "failed": len([c for c in calls if c.status == CallStatus.FAILED]),
        "pending": len([c for c in calls if c.status == CallStatus.PENDING]),
        "avg_duration": round(
            sum(c.duration_seconds or 0 for c in calls) / max(len([c for c in calls if c.duration_seconds]), 1), 1
        ),
    }
