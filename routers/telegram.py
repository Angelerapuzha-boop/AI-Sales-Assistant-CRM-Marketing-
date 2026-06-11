from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.integrations.telegram import telegram_service
from app.models import Company, LeadScore, Meeting, User, UserRole
from app.services.lead_scoring import get_analytics, get_dashboard_stats
from app.services.ai_service import ai_service

router = APIRouter(prefix="/telegram", tags=["Telegram"])


async def _handle_command(command: str, chat_id: str, db: Session) -> str:
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first() or db.query(User).first()
    if not admin:
        return "No users configured. Please register first."

    if command == "/start":
        return """🤖 *AI Sales Assistant CRM Bot*

Welcome! Available commands:
/help - Show all commands
/dashboard - Dashboard stats
/leads - Lead overview
/topleads - Top leads
/companies - Company count
/meetings - Upcoming meetings
/analytics - Analytics summary
/report - Daily report
/generateemail - Email generation help
/health - System health"""

    if command == "/help":
        return "Commands: /start /help /dashboard /leads /topleads /companies /meetings /analytics /report /generateemail /health"

    if command == "/dashboard":
        stats = get_dashboard_stats(db, admin)
        return f"""📊 *Dashboard*
Total Leads: {stats['total_leads']}
Hot: {stats['hot_leads']} | Warm: {stats['warm_leads']} | Cold: {stats['cold_leads']}
Pipeline: ${stats['revenue_pipeline']:,.0f}
Meetings: {stats['meetings_scheduled']}
Emails Sent: {stats['emails_sent']}
Open Rate: {stats['open_rate']}% | Reply Rate: {stats['reply_rate']}%"""

    if command == "/leads":
        leads = db.query(LeadScore).limit(10).all()
        if not leads:
            return "No leads found."
        lines = [f"• Score {l.score}/100 ({l.category.value})" for l in leads]
        return "📋 *Recent Leads*\n" + "\n".join(lines)

    if command == "/topleads":
        leads = db.query(LeadScore).order_by(LeadScore.score.desc()).limit(5).all()
        if not leads:
            return "No leads found."
        lines = [f"🏆 {l.score}/100 - {l.category.value.upper()}" for l in leads]
        return "🔥 *Top Leads*\n" + "\n".join(lines)

    if command == "/companies":
        count = db.query(Company).count()
        return f"🏢 Total Companies: {count}"

    if command == "/meetings":
        meetings = db.query(Meeting).order_by(Meeting.start_time).limit(5).all()
        if not meetings:
            return "No upcoming meetings."
        lines = [f"• {m.title} - {m.start_time.strftime('%Y-%m-%d %H:%M')}" for m in meetings]
        return "📅 *Meetings*\n" + "\n".join(lines)

    if command == "/analytics":
        data = get_analytics(db, admin)
        ld = data["lead_distribution"]
        return f"""📈 *Analytics*
Hot: {ld.get('hot', 0)} | Warm: {ld.get('warm', 0)} | Cold: {ld.get('cold', 0)}
Emails Sent: {data['email_performance']['sent']}
Meetings Scheduled: {data['meeting_analytics']['scheduled']}"""

    if command == "/report":
        stats = get_dashboard_stats(db, admin)
        await telegram_service.notify_daily_report(stats)
        return "Daily report sent!"

    if command.startswith("/generateemail"):
        return "Use the CRM web app to generate emails. Go to Emails > Generate Email."

    if command == "/health":
        return "✅ System is healthy. All services operational."

    return "Unknown command. Type /help for available commands."


@router.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = str(message.get("chat", {}).get("id", ""))

    if not text or not chat_id:
        return {"ok": True}

    db = SessionLocal()
    try:
        command = text.split()[0].lower()
        response = await _handle_command(command, chat_id, db)
        await telegram_service.send_message(chat_id, response)
    finally:
        db.close()

    return {"ok": True}


@router.post("/setup-webhook")
async def setup_webhook():
    return await telegram_service.set_webhook()
