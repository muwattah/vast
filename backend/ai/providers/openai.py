import json
import logging
from typing import Optional
from backend.ai.providers.base import AIProvider
from backend.ai.schemas import AnalysisResult
from backend.ai.prompts import SYSTEM_PROMPT, build_user_prompt, PROMPT_VERSION
from backend.config import get_settings

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    name = "openai"

    def analyze(self, prop_data: dict) -> Optional[AnalysisResult]:
        settings = get_settings()
        if not settings.openai_api_key:
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(prop_data)},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content
            data = json.loads(raw)
            return AnalysisResult.model_validate(data)
        except Exception as e:
            logger.warning(f"OpenAI analysis failed: {e}")
            return None
