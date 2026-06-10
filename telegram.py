from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TelegramService:
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.admin_chat_id = settings.telegram_admin_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> dict:
        if not self.base_url:
            logger.warning("telegram_not_configured")
            return {"success": False, "error": "Telegram not configured", "fallback": True}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                )
                response.raise_for_status()
                return {"success": True}
        except Exception as e:
            logger.error("telegram_send_failed", error=str(e))
            return {"success": False, "error": str(e), "fallback": True}

    async def notify_admin(self, message: str) -> dict:
        if self.admin_chat_id:
            return await self.send_message(self.admin_chat_id, message)
        return {"success": False, "error": "Admin chat ID not configured"}

    async def notify_new_lead(self, company_name: str, score: int) -> dict:
        return await self.notify_admin(f"🔥 *New Lead*\n{company_name}: Score {score}/100")

    async def notify_hot_lead(self, company_name: str) -> dict:
        return await self.notify_admin(f"🚨 *Hot Lead Alert*\n{company_name} is HOT!")

    async def notify_email_sent(self, subject: str) -> dict:
        return await self.notify_admin(f"📧 *Email Sent*\n{subject}")

    async def notify_meeting_scheduled(self, title: str, start_time: str) -> dict:
        return await self.notify_admin(f"📅 *Meeting Scheduled*\n{title}\n{start_time}")

    async def notify_meeting_reminder(self, title: str) -> dict:
        return await self.notify_admin(f"⏰ *Meeting Reminder*\nUpcoming: {title}")

    async def notify_daily_report(self, stats: dict) -> dict:
        text = f"""📊 *Daily Report*
Leads: {stats.get('total_leads', 0)}
Hot: {stats.get('hot_leads', 0)} | Warm: {stats.get('warm_leads', 0)} | Cold: {stats.get('cold_leads', 0)}
Emails Sent: {stats.get('emails_sent', 0)}
Meetings: {stats.get('meetings_scheduled', 0)}"""
        return await self.notify_admin(text)

    async def notify_error(self, error: str) -> dict:
        return await self.notify_admin(f"❌ *Error Alert*\n{error}")

    async def set_webhook(self, url: Optional[str] = None) -> dict:
        webhook_url = url or settings.telegram_webhook_url
        if not self.base_url or not webhook_url:
            return {"success": False, "error": "Webhook URL or bot token not configured"}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.base_url}/setWebhook",
                    json={"url": webhook_url},
                )
                response.raise_for_status()
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error("telegram_webhook_failed", error=str(e))
            return {"success": False, "error": str(e)}


telegram_service = TelegramService()
