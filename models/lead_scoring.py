from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    BuyingSignal,
    Company,
    Contact,
    Email,
    EmailStatus,
    LeadCategory,
    LeadScore,
    Meeting,
    MeetingStatus,
    User,
    UserRole,
)


INDUSTRY_SCORES = {
    "technology": 20,
    "software": 20,
    "saas": 22,
    "finance": 18,
    "healthcare": 16,
    "manufacturing": 14,
    "retail": 12,
    "education": 10,
}

SENIORITY_SCORES = {
    "c-level": 20,
    "vp": 18,
    "director": 15,
    "manager": 10,
    "individual": 5,
}


def _score_revenue(revenue: float | None) -> int:
    if not revenue:
        return 5
    if revenue >= 10_000_000:
        return 20
    if revenue >= 1_000_000:
        return 15
    if revenue >= 100_000:
        return 10
    return 5


def _score_employees(count: int | None) -> int:
    if not count:
        return 5
    if count >= 500:
        return 15
    if count >= 100:
        return 12
    if count >= 20:
        return 8
    return 5


def _score_industry(industry: str | None) -> int:
    if not industry:
        return 5
    return INDUSTRY_SCORES.get(industry.lower(), 8)


def _score_seniority(seniority: str | None) -> int:
    if not seniority:
        return 5
    return SENIORITY_SCORES.get(seniority.lower(), 5)


def _score_signals(db: Session, company_id: UUID) -> int:
    signals = db.query(BuyingSignal).filter(BuyingSignal.company_id == company_id).all()
    if not signals:
        return 0
    total = sum(s.strength for s in signals)
    return min(20, total)


def _score_email_activity(db: Session, company_id: UUID) -> int:
    emails = db.query(Email).filter(Email.company_id == company_id).all()
    if not emails:
        return 0
    sent = len([e for e in emails if e.status == EmailStatus.SENT])
    opened = len([e for e in emails if e.opened_at])
    replied = len([e for e in emails if e.replied_at])
    score = min(5, sent) + min(10, opened * 2) + min(10, replied * 5)
    return min(20, score)


def _category_from_score(score: int) -> LeadCategory:
    if score >= 70:
        return LeadCategory.HOT
    if score >= 40:
        return LeadCategory.WARM
    return LeadCategory.COLD


def calculate_lead_score(
    db: Session, company: Company, contact: Contact | None = None
) -> LeadScore:
    revenue_score = _score_revenue(company.revenue)
    employee_score = _score_employees(company.employee_count)
    industry_score = _score_industry(company.industry)
    signal_score = _score_signals(db, company.id)
    email_score = _score_email_activity(db, company.id)
    seniority_score = _score_seniority(contact.seniority if contact else None)

    total = min(100, revenue_score + employee_score + industry_score + signal_score + email_score + seniority_score)
    category = _category_from_score(total)

    existing = (
        db.query(LeadScore)
        .filter(LeadScore.company_id == company.id, LeadScore.contact_id == (contact.id if contact else None))
        .first()
    )
    factors = {
        "revenue": revenue_score,
        "employees": employee_score,
        "industry": industry_score,
        "signals": signal_score,
        "email": email_score,
        "seniority": seniority_score,
    }

    if existing:
        existing.score = total
        existing.category = category
        existing.revenue_score = revenue_score
        existing.employee_score = employee_score
        existing.industry_score = industry_score
        existing.signal_score = signal_score
        existing.email_score = email_score
        existing.seniority_score = seniority_score
        existing.factors = factors
        db.commit()
        db.refresh(existing)
        return existing

    lead_score = LeadScore(
        company_id=company.id,
        contact_id=contact.id if contact else None,
        score=total,
        category=category,
        revenue_score=revenue_score,
        employee_score=employee_score,
        industry_score=industry_score,
        signal_score=signal_score,
        email_score=email_score,
        seniority_score=seniority_score,
        factors=factors,
    )
    db.add(lead_score)
    db.commit()
    db.refresh(lead_score)
    return lead_score


def get_user_filter(user: User):
    if user.role == UserRole.ADMIN:
        return lambda q: q
    return lambda q: q.filter(
        (Company.owner_id == user.id) if hasattr(q.column_descriptions[0]["type"], "owner_id") else True
    )


def get_dashboard_stats(db: Session, user: User) -> dict:
    company_query = db.query(Company)
    if user.role != UserRole.ADMIN:
        company_query = company_query.filter(Company.owner_id == user.id)
    companies = company_query.all()
    company_ids = [c.id for c in companies]

    lead_query = db.query(LeadScore).filter(LeadScore.company_id.in_(company_ids)) if company_ids else db.query(LeadScore).filter(False)
    leads = lead_query.all()

    hot = len([l for l in leads if l.category == LeadCategory.HOT])
    warm = len([l for l in leads if l.category == LeadCategory.WARM])
    cold = len([l for l in leads if l.category == LeadCategory.COLD])

    revenue = sum(c.revenue or 0 for c in companies)

    meeting_query = db.query(Meeting).filter(Meeting.status == MeetingStatus.SCHEDULED)
    if user.role != UserRole.ADMIN:
        meeting_query = meeting_query.filter(Meeting.organizer_id == user.id)
    meetings_count = meeting_query.count()

    email_query = db.query(Email).filter(Email.status == EmailStatus.SENT)
    if user.role != UserRole.ADMIN:
        email_query = email_query.filter(Email.sender_id == user.id)
    sent_emails = email_query.all()
    emails_sent = len(sent_emails)
    opened = len([e for e in sent_emails if e.opened_at])
    replied = len([e for e in sent_emails if e.replied_at])
    open_rate = (opened / emails_sent * 100) if emails_sent else 0
    reply_rate = (replied / emails_sent * 100) if emails_sent else 0

    recent = []
    recent_emails = email_query.order_by(Email.created_at.desc()).limit(5).all()
    for e in recent_emails:
        recent.append({"type": "email", "action": f"Email sent: {e.subject}", "timestamp": e.created_at.isoformat()})

    recent_meetings = meeting_query.order_by(Meeting.created_at.desc()).limit(5).all()
    for m in recent_meetings:
        recent.append({"type": "meeting", "action": f"Meeting: {m.title}", "timestamp": m.created_at.isoformat()})

    recent.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "total_leads": len(leads),
        "hot_leads": hot,
        "warm_leads": warm,
        "cold_leads": cold,
        "revenue_pipeline": revenue,
        "meetings_scheduled": meetings_count,
        "emails_sent": emails_sent,
        "open_rate": round(open_rate, 1),
        "reply_rate": round(reply_rate, 1),
        "recent_activities": recent[:10],
    }


def get_analytics(db: Session, user: User) -> dict:
    company_query = db.query(Company)
    if user.role != UserRole.ADMIN:
        company_query = company_query.filter(Company.owner_id == user.id)
    companies = company_query.all()
    company_ids = [c.id for c in companies]

    leads = db.query(LeadScore).filter(LeadScore.company_id.in_(company_ids)).all() if company_ids else []
    lead_dist = {"hot": 0, "warm": 0, "cold": 0}
    for l in leads:
        lead_dist[l.category.value] += 1

    email_query = db.query(Email)
    if user.role != UserRole.ADMIN:
        email_query = email_query.filter(Email.sender_id == user.id)
    emails = email_query.all()
    sent = [e for e in emails if e.status == EmailStatus.SENT]

    revenue_by_industry = {}
    for c in companies:
        ind = c.industry or "Other"
        revenue_by_industry[ind] = revenue_by_industry.get(ind, 0) + (c.revenue or 0)

    meeting_query = db.query(Meeting)
    if user.role != UserRole.ADMIN:
        meeting_query = meeting_query.filter(Meeting.organizer_id == user.id)
    meetings = meeting_query.all()

    return {
        "lead_distribution": lead_dist,
        "email_performance": {
            "sent": len(sent),
            "opened": len([e for e in sent if e.opened_at]),
            "replied": len([e for e in sent if e.replied_at]),
            "failed": len([e for e in emails if e.status == EmailStatus.FAILED]),
        },
        "revenue_pipeline": revenue_by_industry,
        "conversion_funnel": {
            "leads": len(leads),
            "contacted": len(set(e.company_id for e in sent if e.company_id)),
            "meetings": len(meetings),
            "qualified": len([l for l in leads if l.category == LeadCategory.HOT]),
        },
        "meeting_analytics": {
            "scheduled": len([m for m in meetings if m.status == MeetingStatus.SCHEDULED]),
            "completed": len([m for m in meetings if m.status == MeetingStatus.COMPLETED]),
            "cancelled": len([m for m in meetings if m.status == MeetingStatus.CANCELLED]),
        },
    }
