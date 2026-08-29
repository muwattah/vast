import json
import logging
from typing import Optional
from backend.ai.providers.base import AIProvider
from backend.ai.schemas import AnalysisResult
from backend.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.config import get_settings

logger = logging.getLogger(__name__)


class GrokProvider(AIProvider):
    name = "grok"

    def analyze(self, prop_data: dict) -> Optional[AnalysisResult]:
        settings = get_settings()
        if not settings.grok_api_key:
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.grok_api_key, base_url="https://api.x.ai/v1")
            resp = client.chat.completions.create(
                model="grok-2-latest",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(prop_data)},
                ],
                temperature=0.2,
            )
            raw = resp.choices[0].message.content
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            return AnalysisResult.model_validate(data)
        except Exception as e:
            logger.warning(f"Grok analysis failed: {e}")
            return None
