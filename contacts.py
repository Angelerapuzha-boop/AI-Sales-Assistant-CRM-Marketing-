import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, Contact, User, UserRole
from app.schemas import ContactCreate, ContactResponse, ContactUpdate, PaginatedResponse
from app.services.lead_scoring import calculate_lead_score
from app.utils.security import get_current_user

router = APIRouter(prefix="/contacts", tags=["Contacts"])


def _contact_query(db: Session, user: User):
    q = db.query(Contact)
    if user.role != UserRole.ADMIN:
        q = q.filter(Contact.owner_id == user.id)
    return q


@router.get("", response_model=PaginatedResponse)
def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    company_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _contact_query(db, current_user)
    if search:
        query = query.filter(
            (Contact.first_name.ilike(f"%{search}%"))
            | (Contact.last_name.ilike(f"%{search}%"))
            | (Contact.email.ilike(f"%{search}%"))
        )
    if company_id:
        query = query.filter(Contact.company_id == company_id)
    total = query.count()
    items = query.order_by(Contact.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[ContactResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=ContactResponse, status_code=201)
def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.company_id:
        company = db.query(Company).filter(Company.id == data.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
    contact = Contact(owner_id=current_user.id, **data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    if contact.company_id:
        company = db.query(Company).filter(Company.id == contact.company_id).first()
        if company:
            calculate_lead_score(db, company, contact)
    return ContactResponse.model_validate(contact)


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = _contact_query(db, current_user).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse.model_validate(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = _contact_query(db, current_user).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    if contact.company_id:
        company = db.query(Company).filter(Company.id == contact.company_id).first()
        if company:
            calculate_lead_score(db, company, contact)
    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}", status_code=204)
def delete_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = _contact_query(db, current_user).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
