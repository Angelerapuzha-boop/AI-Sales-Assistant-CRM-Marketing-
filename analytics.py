from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification, User, UserRole
from app.schemas import AnalyticsResponse, DashboardStats, NotificationResponse, PaginatedResponse
from app.services.csv_import import import_companies_csv, import_contacts_csv
from app.services.lead_scoring import get_analytics, get_dashboard_stats
from app.utils.security import get_current_user

router = APIRouter(tags=["Analytics & Import"])


@router.get("/analytics/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_dashboard_stats(db, current_user)


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_analytics(db, current_user)


@router.get("/notifications", response_model=PaginatedResponse)
def list_notifications(
    page: int = 1,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    total = query.count()
    items = query.order_by(Notification.created_at.desc()).offset((page - 1) * 20).limit(20).all()
    return PaginatedResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=20,
        pages=(total + 19) // 20,
    )


@router.put("/notifications/{notification_id}/read")
def mark_read(notification_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notification = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == current_user.id
    ).first()
    if notification:
        notification.is_read = True
        db.commit()
    return {"success": True}


@router.put("/notifications/read-all")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).update(
        {"is_read": True}
    )
    db.commit()
    return {"success": True}


@router.post("/import/companies")
async def import_companies(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    return import_companies_csv(db, current_user, content)


@router.post("/import/contacts")
async def import_contacts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    return import_contacts_csv(db, current_user, content)
