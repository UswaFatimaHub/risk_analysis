import logging
from typing import Optional, Type
from openai import AsyncOpenAI
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with the Omni LLM server"""

    def __init__(self):
        self.model = settings.omni_model
        self.base_url = settings.omni_base_url
        self.api_key = settings.omni_api_key
        self.client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
        logger.info(f"LLM Service initialized with model: {self.model} on {self.base_url}")

    async def parse_response(
        self,
        schema: Type[BaseModel],
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> Optional[BaseModel]:
        """Generate a structured response validated by a Pydantic schema"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(max_retries):
            try:
                response = await self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=messages,
                    response_format=schema,
                )
                return response.choices[0].message.parsed

            except Exception as e:
                logger.error(f"LLM JSON parse failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to parse response after {max_retries} attempts")
                    return None

        return None
