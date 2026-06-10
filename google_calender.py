from datetime import datetime
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class GoogleCalendarService:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self):
        self.api_key = settings.google_calendar_api_key
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret

    def _get_service(self, tokens: dict):
        creds = Credentials(
            token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.SCOPES,
        )
        return build("calendar", "v3", credentials=creds, developerKey=self.api_key or None)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_event(
        self,
        tokens: dict,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        attendees: Optional[list[str]] = None,
        location: Optional[str] = None,
    ) -> dict:
        try:
            service = self._get_service(tokens)
            event = {
                "summary": title,
                "description": description or "",
                "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
            }
            if location:
                event["location"] = location
            if attendees:
                event["attendees"] = [{"email": a} for a in attendees]
            result = service.events().insert(calendarId="primary", body=event).execute()
            logger.info("calendar_event_created", event_id=result.get("id"))
            return {"success": True, "event_id": result.get("id"), "link": result.get("htmlLink")}
        except Exception as e:
            logger.error("calendar_create_failed", error=str(e))
            return {"success": False, "error": str(e), "fallback": True}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def update_event(self, tokens: dict, event_id: str, updates: dict) -> dict:
        try:
            service = self._get_service(tokens)
            event = service.events().get(calendarId="primary", eventId=event_id).execute()
            event.update(updates)
            result = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
            return {"success": True, "event_id": result.get("id")}
        except Exception as e:
            logger.error("calendar_update_failed", error=str(e))
            return {"success": False, "error": str(e)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def delete_event(self, tokens: dict, event_id: str) -> dict:
        try:
            service = self._get_service(tokens)
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            return {"success": True}
        except Exception as e:
            logger.error("calendar_delete_failed", error=str(e))
            return {"success": False, "error": str(e)}

    def list_events(self, tokens: dict, max_results: int = 10) -> list:
        try:
            service = self._get_service(tokens)
            result = service.events().list(calendarId="primary", maxResults=max_results, singleEvents=True, orderBy="startTime").execute()
            return result.get("items", [])
        except Exception as e:
            logger.error("calendar_list_failed", error=str(e))
            return []


calendar_service = GoogleCalendarService()
