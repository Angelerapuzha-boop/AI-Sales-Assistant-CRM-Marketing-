import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.rate_limit import limiter
from app.models import BuyingSignal, Company, LeadCategory, User, UserRole
from app.schemas import CompanyCreate, CompanyResponse, CompanyUpdate, PaginatedResponse
from app.services.ai_service import ai_service
from app.services.lead_scoring import calculate_lead_score
from app.utils.audit import log_audit
from app.utils.security import get_current_user

router = APIRouter(prefix="/companies", tags=["Companies"])


def _company_query(db: Session, user: User):
    q = db.query(Company)
    if user.role != UserRole.ADMIN:
        q = q.filter(Company.owner_id == user.id)
    return q


@router.get("", response_model=PaginatedResponse)
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    industry: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _company_query(db, current_user)
    if search:
        query = query.filter(Company.name.ilike(f"%{search}%"))
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    total = query.count()
    items = query.order_by(Company.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[CompanyResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=CompanyResponse, status_code=201)
@limiter.limit("30/minute")
def create_company(
    request: Request,
    data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = Company(owner_id=current_user.id, **data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    calculate_lead_score(db, company)
    log_audit(db, "create", "company", company.id, current_user.id, request=request)
    return CompanyResponse.model_validate(company)


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = _company_query(db, current_user).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse.model_validate(company)


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _company_query(db, current_user).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    calculate_lead_score(db, company)
    return CompanyResponse.model_validate(company)


@router.delete("/{company_id}", status_code=204)
def delete_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _company_query(db, current_user).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()


@router.post("/{company_id}/ai-summary")
def generate_ai_summary(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _company_query(db, current_user).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company_data = {
        "name": company.name,
        "industry": company.industry,
        "revenue": company.revenue,
        "employee_count": company.employee_count,
        "description": company.description,
    }
    summary, provider = ai_service.generate_company_summary(company_data)
    company.ai_summary = summary
    db.commit()
    return {"summary": summary, "provider": provider}


@router.post("/{company_id}/buying-signals")
def generate_buying_signals(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _company_query(db, current_user).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    content, provider = ai_service.generate_buying_signals(
        {"name": company.name, "industry": company.industry, "revenue": company.revenue}
    )
    signal = BuyingSignal(
        company_id=company.id,
        signal_type="ai_generated",
        description=content,
        strength=8,
        source=provider,
    )
    db.add(signal)
    db.commit()
    calculate_lead_score(db, company)
    return {"signals": content, "provider": provider}
