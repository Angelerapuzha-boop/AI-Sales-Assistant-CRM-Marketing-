from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

EMAIL_TEMPLATES = {
    "cold": """Subject: Quick question about {company_name}

Hi {contact_name},

I noticed {company_name} is doing great work in {industry}. We help companies like yours streamline sales operations and increase pipeline velocity.

Would you be open to a brief 15-minute call this week to explore if there's a fit?

Best regards,
{sender_name}""",
    "follow_up": """Subject: Following up - {company_name}

Hi {contact_name},

I wanted to follow up on my previous email. I understand you're busy, but I believe our solution could help {company_name} achieve significant ROI.

Would a quick call work for you?

Best,
{sender_name}""",
    "meeting_request": """Subject: Meeting Request - {company_name}

Hi {contact_name},

I'd love to schedule a meeting to discuss how we can support {company_name}'s growth objectives.

Please let me know your availability this week.

Best regards,
{sender_name}""",
}


class AIService:
    def __init__(self):
        self.groq_client = None
        self.openai_client = None
        self._init_clients()

    def _init_clients(self):
        if settings.groq_api_key:
            try:
                from groq import Groq

                self.groq_client = Groq(api_key=settings.groq_api_key)
            except Exception as e:
                logger.warning("groq_init_failed", error=str(e))
        if settings.openai_api_key:
            try:
                from openai import OpenAI

                self.openai_client = OpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                logger.warning("openai_init_failed", error=str(e))

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    def _call_groq(self, prompt: str, system: str = "You are a sales AI assistant.") -> str:
        if not self.groq_client:
            raise RuntimeError("Groq client not available")
        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    def _call_openai(self, prompt: str, system: str = "You are a sales AI assistant.") -> str:
        if not self.openai_client:
            raise RuntimeError("OpenAI client not available")
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""

    def generate(self, prompt: str, system: str = "You are a sales AI assistant.") -> tuple[str, str]:
        providers = []
        if settings.ai_primary_provider == "groq":
            providers = ["groq", "openai", "template"]
        else:
            providers = ["openai", "groq", "template"]

        for provider in providers:
            try:
                if provider == "groq":
                    return self._call_groq(prompt, system), "groq"
                if provider == "openai":
                    return self._call_openai(prompt, system), "openai"
            except Exception as e:
                logger.warning("ai_provider_failed", provider=provider, error=str(e))
                continue

        return self._template_fallback(prompt), "template"

    def _template_fallback(self, prompt: str) -> str:
        return f"[Template Response] Based on available data: {prompt[:500]}... Please review and customize this content."

    def generate_company_summary(self, company_data: dict) -> tuple[str, str]:
        prompt = f"""Generate a concise company summary for sales purposes:
Company: {company_data.get('name')}
Industry: {company_data.get('industry', 'Unknown')}
Revenue: ${company_data.get('revenue', 'Unknown')}
Employees: {company_data.get('employee_count', 'Unknown')}
Description: {company_data.get('description', 'N/A')}"""
        return self.generate(prompt, "You are a B2B sales intelligence analyst.")

    def generate_buying_signals(self, company_data: dict) -> tuple[str, str]:
        prompt = f"""Identify 3-5 buying signals for this company:
{company_data}"""
        return self.generate(prompt, "You identify B2B buying signals and intent data.")

    def generate_sales_insights(self, company_data: dict, lead_score: int) -> tuple[str, str]:
        prompt = f"""Provide actionable sales insights:
Company: {company_data}
Lead Score: {lead_score}/100"""
        return self.generate(prompt, "You are a senior sales strategist.")

    def generate_email(
        self, email_type: str, company_name: str, contact_name: str, industry: str, sender_name: str, context: str = ""
    ) -> tuple[str, str]:
        template = EMAIL_TEMPLATES.get(email_type, EMAIL_TEMPLATES["cold"])
        fallback = template.format(
            company_name=company_name,
            contact_name=contact_name,
            industry=industry or "your industry",
            sender_name=sender_name,
        )
        prompt = f"""Write a professional {email_type} sales email.
Company: {company_name}
Contact: {contact_name}
Industry: {industry}
Context: {context}
Return subject on first line, then body."""
        try:
            result, provider = self.generate(prompt)
            return result, provider
        except Exception:
            return fallback, "template"

    def generate_meeting_prep(self, meeting_data: dict, company_data: dict) -> tuple[str, str]:
        prompt = f"""Generate meeting preparation notes:
Meeting: {meeting_data}
Company: {company_data}"""
        return self.generate(prompt, "You prepare sales meeting briefings.")


ai_service = AIService()
