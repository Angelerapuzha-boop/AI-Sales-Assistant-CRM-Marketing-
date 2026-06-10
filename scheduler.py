from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.integrations.telegram import telegram_service
from app.models import Meeting, MeetingStatus, User
from app.services.lead_scoring import get_dashboard_stats
from app.services.notification_service import notify_meeting_reminder
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
scheduler = BackgroundScheduler()


def check_meeting_reminders():
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        reminder_window = now + timedelta(minutes=settings.meeting_reminder_minutes)
        meetings = (
            db.query(Meeting)
            .filter(
                Meeting.status == MeetingStatus.SCHEDULED,
                Meeting.reminder_sent == False,
                Meeting.start_time <= reminder_window,
                Meeting.start_time > now,
            )
            .all()
        )
        for meeting in meetings:
            notify_meeting_reminder(db, meeting.organizer_id, meeting.title)
            meeting.reminder_sent = True
        if meetings:
            db.commit()
    except Exception as e:
        logger.error("meeting_reminder_failed", error=str(e))
    finally:
        db.close()


async def send_daily_report():
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        if admin:
            stats = get_dashboard_stats(db, admin)
            await telegram_service.notify_daily_report(stats)
    except Exception as e:
        logger.error("daily_report_failed", error=str(e))
    finally:
        db.close()


def run_daily_report():
    import asyncio

    asyncio.run(send_daily_report())


def start_scheduler():
    if not settings.scheduler_enabled:
        return
    scheduler.add_job(check_meeting_reminders, "interval", minutes=5, id="meeting_reminders")
    scheduler.add_job(run_daily_report, "cron", hour=settings.daily_report_hour, id="daily_report")
    scheduler.start()
    logger.info("scheduler_started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
