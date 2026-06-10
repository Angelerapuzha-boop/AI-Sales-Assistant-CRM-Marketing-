from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.integrations.bland_ai import bland_ai_service
from app.integrations.gmail import gmail_service
from app.integrations.google_calendar import calendar_service
from app.integrations.telegram import telegram_service
from app.services.ai_service import ai_service

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": db_status,
            "ai_groq": "configured" if settings.groq_api_key else "not_configured",
            "ai_openai": "configured" if settings.openai_api_key else "not_configured",
            "gmail": "configured" if settings.gmail_api_key else "not_configured",
            "calendar": "configured" if settings.google_calendar_api_key else "not_configured",
            "telegram": "configured" if telegram_service.is_configured else "not_configured",
            "bland_ai": "configured" if settings.bland_ai_api_key else "not_configured",
        },
    }


@router.get("/status")
def status():
    return {
        "app": settings.app_name,
        "environment": settings.app_env,
        "version": "1.0.0",
        "uptime_check": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/info")
def info():
    return {
        "name": settings.app_name,
        "description": "Production-ready AI Sales Assistant CRM",
        "features": [
            "Lead Scoring",
            "AI Email Generation",
            "Gmail Integration",
            "Google Calendar",
            "Bland AI Calls",
            "Telegram Bot",
            "Analytics Dashboard",
            "CSV Import",
        ],
        "api_docs": "/docs",
    }
