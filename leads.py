import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.telegram import telegram_service
from app.models import Company, Contact, LeadCategory, LeadScore, User, UserRole
from app.schemas import AIInsightRequest, LeadScoreResponse, PaginatedResponse
from app.services.ai_service import ai_service
from app.services.lead_scoring import calculate_lead_score
from app.services.notification_service import notify_hot_lead, notify_new_lead
from app.utils.security import get_current_user

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=PaginatedResponse)
def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: LeadCategory | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(LeadScore)
    if current_user.role != UserRole.ADMIN:
        company_ids = [c.id for c in db.query(Company).filter(Company.owner_id == current_user.id).all()]
        query = query.filter(LeadScore.company_id.in_(company_ids)) if company_ids else query.filter(False)
    if category:
        query = query.filter(LeadScore.category == category)
    total = query.count()
    items = query.order_by(LeadScore.score.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[LeadScoreResponse.model_validate(l) for l in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/top", response_model=list[LeadScoreResponse])
def top_leads(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(LeadScore)
    if current_user.role != UserRole.ADMIN:
        company_ids = [c.id for c in db.query(Company).filter(Company.owner_id == current_user.id).all()]
        query = query.filter(LeadScore.company_id.in_(company_ids)) if company_ids else query.filter(False)
    leads = query.order_by(LeadScore.score.desc()).limit(limit).all()
    return [LeadScoreResponse.model_validate(l) for l in leads]


@router.post("/recalculate/{company_id}", response_model=LeadScoreResponse)
async def recalculate_lead(
    company_id: UUID,
    contact_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if current_user.role != UserRole.ADMIN and company.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    contact = db.query(Contact).filter(Contact.id == contact_id).first() if contact_id else None
    previous = db.query(LeadScore).filter(LeadScore.company_id == company_id).first()
    prev_category = previous.category if previous else None
    lead_score = calculate_lead_score(db, company, contact)
    notify_new_lead(db, company.owner_id, company.name, lead_score.score)
    if lead_score.category == LeadCategory.HOT and prev_category != LeadCategory.HOT:
        notify_hot_lead(db, company.owner_id, company.name)
        await telegram_service.notify_hot_lead(company.name)
    return LeadScoreResponse.model_validate(lead_score)


@router.post("/insights")
def get_sales_insights(
    data: AIInsightRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    lead = db.query(LeadScore).filter(LeadScore.company_id == company.id).first()
    score = lead.score if lead else 0
    insights, provider = ai_service.generate_sales_insights(
        {"name": company.name, "industry": company.industry, "revenue": company.revenue},
        score,
    )
    return {"insights": insights, "provider": provider, "lead_score": score}
