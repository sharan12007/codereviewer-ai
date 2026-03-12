import asyncio
import json
import logging
from config import settings

logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.1-8b-instant"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
GEMINI_MODEL = "gemini-2.0-flash"


class ReviewPipelineError(Exception):
    pass


class LLMClient:
    def __init__(self):
        self.provider = None
        self.client = None

        # Priority 1 — Groq (free tier, fast)
        if settings.GROQ_API_KEY:
            try:
                from groq import Groq
                self.client = Groq(api_key=settings.GROQ_API_KEY)
                self.provider = "groq"
                logger.info(f"LLMClient: using Groq ({GROQ_MODEL})")
            except Exception as e:
                logger.error(f"Failed to init Groq: {e}")

        # Priority 2 — Anthropic
        if not self.provider and settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                self.provider = "anthropic"
                logger.info(f"LLMClient: using Anthropic ({ANTHROPIC_MODEL})")
            except Exception as e:
                logger.error(f"Failed to init Anthropic: {e}")

        # Priority 3 — Gemini
        if not self.provider and settings.GOOGLE_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                self.provider = "gemini"
                self.genai = genai
                logger.info(f"LLMClient: using Gemini ({GEMINI_MODEL})")
            except Exception as e:
                logger.error(f"Failed to init Gemini: {e}")

        if not self.provider:
            raise ReviewPipelineError(
                "No LLM API key found. Set GROQ_API_KEY, GOOGLE_API_KEY or ANTHROPIC_API_KEY in .env"
            )

    def _parse_json(self, raw: str) -> dict:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()
        return json.loads(cleaned)

    async def _call_groq(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0.2,
            max_tokens=2048,
        )
        return response.choices[0].message.content

    async def _call_anthropic(self, system: str, user: str) -> str:
        response = self.client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return response.content[0].text

    async def _call_gemini(self, system: str, user: str) -> str:
        model = self.genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=system
        )
        response = model.generate_content(
            user,
            generation_config={"temperature": 0.2}
        )
        return response.text

    async def review(self, system: str, user: str) -> dict:
        for attempt in range(2):
            try:
                if self.provider == "groq":
                    raw = await self._call_groq(system, user)
                elif self.provider == "anthropic":
                    raw = await self._call_anthropic(system, user)
                else:
                    raw = await self._call_gemini(system, user)

                try:
                    return self._parse_json(raw)
                except json.JSONDecodeError:
                    if attempt == 0:
                        logger.warning("JSON parse failed, retrying with stricter instruction")
                        user = user + "\n\nReturn ONLY valid JSON. Your previous response was not valid JSON."
                        continue
                    else:
                        logger.error(f"Raw LLM response: {raw}")
                        return {"summary": "Failed to parse LLM response.", "comments": []}

            except Exception as e:
                err_str = str(e)
                if "429" in err_str and attempt == 0:
                    logger.warning("Rate limited (429), waiting 5s and retrying")
                    await asyncio.sleep(5)
                    continue
                raise ReviewPipelineError(f"LLM API error: {e}")

        return {"summary": "LLM call failed after retries.", "comments": []}

    def get_model_name(self) -> str:
        if self.provider == "groq":
            return GROQ_MODEL
        if self.provider == "anthropic":
            return ANTHROPIC_MODEL
        return GEMINI_MODEL