import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BlandAIService:
    def __init__(self):
        self.api_key = settings.bland_ai_api_key
        self.base_url = settings.bland_ai_base_url

    @property
    def _headers(self) -> dict:
        return {"Authorization": self.api_key, "Content-Type": "application/json"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def initiate_call(
        self,
        phone_number: str,
        task: str,
        voice: str = "maya",
        max_duration: int = 300,
    ) -> dict:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/calls",
                    headers=self._headers,
                    json={
                        "phone_number": phone_number,
                        "task": task,
                        "voice": voice,
                        "max_duration": max_duration,
                        "reduce_latency": True,
                    },
                )
                response.raise_for_status()
                data = response.json()
                logger.info("bland_call_initiated", call_id=data.get("call_id"))
                return {"success": True, "call_id": data.get("call_id"), "data": data}
        except Exception as e:
            logger.error("bland_call_failed", error=str(e))
            return {"success": False, "error": str(e), "fallback": True}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_call_details(self, call_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/calls/{call_id}",
                    headers=self._headers,
                )
                response.raise_for_status()
                return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error("bland_call_details_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def schedule_call(self, phone_number: str, task: str, scheduled_at: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/calls",
                    headers=self._headers,
                    json={
                        "phone_number": phone_number,
                        "task": task,
                        "start_time": scheduled_at,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return {"success": True, "call_id": data.get("call_id"), "data": data}
        except Exception as e:
            logger.error("bland_schedule_failed", error=str(e))
            return {"success": False, "error": str(e)}


bland_ai_service = BlandAIService()
