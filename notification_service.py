from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Notification, NotificationType, User


def create_notification(
    db: Session,
    user_id: UUID,
    notification_type: NotificationType,
    title: str,
    message: str,
    metadata: dict | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        metadata_=metadata,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def notify_new_lead(db: Session, user_id: UUID, company_name: str, score: int):
    return create_notification(
        db,
        user_id,
        NotificationType.NEW_LEAD,
        "New Lead",
        f"New lead scored for {company_name}: {score}/100",
        {"company_name": company_name, "score": score},
    )


def notify_hot_lead(db: Session, user_id: UUID, company_name: str):
    return create_notification(
        db,
        user_id,
        NotificationType.HOT_LEAD,
        "Hot Lead Alert",
        f"{company_name} is now a HOT lead!",
        {"company_name": company_name},
    )


def notify_email_sent(db: Session, user_id: UUID, subject: str):
    return create_notification(
        db,
        user_id,
        NotificationType.EMAIL_SENT,
        "Email Sent",
        f"Email sent: {subject}",
        {"subject": subject},
    )


def notify_meeting_scheduled(db: Session, user_id: UUID, title: str, start_time: str):
    return create_notification(
        db,
        user_id,
        NotificationType.MEETING_SCHEDULED,
        "Meeting Scheduled",
        f"Meeting '{title}' scheduled for {start_time}",
        {"title": title, "start_time": start_time},
    )


def notify_meeting_reminder(db: Session, user_id: UUID, title: str):
    return create_notification(
        db,
        user_id,
        NotificationType.MEETING_REMINDER,
        "Meeting Reminder",
        f"Upcoming meeting: {title}",
        {"title": title},
    )


def notify_error(db: Session, user_id: UUID, error_message: str):
    return create_notification(
        db,
        user_id,
        NotificationType.ERROR_ALERT,
        "System Error",
        error_message,
        {"error": error_message},
    )
