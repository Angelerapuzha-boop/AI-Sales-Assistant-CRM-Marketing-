from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import LeadCategory, UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = UserRole.SALES_REP


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    revenue: Optional[float] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    revenue: Optional[float] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None


class CompanyResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    revenue: Optional[float] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None
    ai_summary: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactCreate(BaseModel):
    company_id: Optional[UUID] = None
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    is_primary: bool = False


class ContactUpdate(BaseModel):
    company_id: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    is_primary: Optional[bool] = None


class ContactResponse(BaseModel):
    id: UUID
    owner_id: UUID
    company_id: Optional[UUID] = None
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    seniority: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadScoreResponse(BaseModel):
    id: UUID
    company_id: UUID
    contact_id: Optional[UUID] = None
    score: int
    category: LeadCategory
    revenue_score: int
    employee_score: int
    industry_score: int
    signal_score: int
    email_score: int
    seniority_score: int
    factors: Optional[dict] = None
    calculated_at: datetime

    model_config = {"from_attributes": True}


class BuyingSignalResponse(BaseModel):
    id: UUID
    company_id: UUID
    signal_type: str
    description: str
    strength: int
    source: str
    detected_at: datetime

    model_config = {"from_attributes": True}


class EmailCreate(BaseModel):
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    subject: str
    body: str
    email_type: str = "cold"


class EmailGenerateRequest(BaseModel):
    company_id: UUID
    contact_id: Optional[UUID] = None
    email_type: str = "cold"
    context: Optional[str] = None


class EmailResponse(BaseModel):
    id: UUID
    sender_id: UUID
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    subject: str
    body: str
    email_type: str
    status: str
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MeetingCreate(BaseModel):
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    meeting_link: Optional[str] = None


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    status: Optional[str] = None


class MeetingResponse(BaseModel):
    id: UUID
    organizer_id: UUID
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    status: str
    prep_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CallCreate(BaseModel):
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    phone_number: str
    scheduled_at: Optional[datetime] = None


class CallResponse(BaseModel):
    id: UUID
    user_id: UUID
    company_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    phone_number: str
    direction: str
    status: str
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    qualification_result: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    message: str
    is_read: bool
    metadata: Optional[dict] = Field(None, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class DashboardStats(BaseModel):
    total_leads: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    revenue_pipeline: float
    meetings_scheduled: int
    emails_sent: int
    open_rate: float
    reply_rate: float
    recent_activities: list[dict]


class AnalyticsResponse(BaseModel):
    lead_distribution: dict
    email_performance: dict
    revenue_pipeline: dict
    conversion_funnel: dict
    meeting_analytics: dict


class AIInsightRequest(BaseModel):
    company_id: UUID
    insight_type: str = "sales_insights"


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int
