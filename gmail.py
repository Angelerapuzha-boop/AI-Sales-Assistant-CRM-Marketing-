import base64
from email.mime.text import MIMEText
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class GmailService:
    SCOPES = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(self):
        self.api_key = settings.gmail_api_key
        self.client_id = settings.gmail_client_id or settings.google_client_id
        self.client_secret = settings.gmail_client_secret or settings.google_client_secret

    def _get_service(self, tokens: dict):
        creds = Credentials(
            token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.SCOPES,
        )
        return build("gmail", "v1", credentials=creds, developerKey=self.api_key or None)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def send_email(
        self,
        tokens: dict,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
    ) -> dict:
        try:
            service = self._get_service(tokens)
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            if from_email:
                message["from"] = from_email
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
            logger.info("gmail_sent", message_id=result.get("id"))
            return {"success": True, "message_id": result.get("id"), "thread_id": result.get("threadId")}
        except Exception as e:
            logger.error("gmail_send_failed", error=str(e))
            return {"success": False, "error": str(e), "fallback": True}

    def get_messages(self, tokens: dict, max_results: int = 10) -> list:
        try:
            service = self._get_service(tokens)
            results = service.users().messages().list(userId="me", maxResults=max_results).execute()
            return results.get("messages", [])
        except Exception as e:
            logger.error("gmail_list_failed", error=str(e))
            return []


gmail_service = GmailService()
