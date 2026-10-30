import os
from typing import Optional, Dict, Any, List
from app.ai.base import AIProvider
from app.ai.local_provider import SmartLocalAIProvider
from app.schemas.ai import AIUnderstandingResult
from app.core.config import settings

class RealAIProvider(AIProvider):
    def __init__(self):
        self.fallback = SmartLocalAIProvider()
        self.api_key = settings.OPENAI_API_KEY or settings.GEMINI_API_KEY

    async def understand_entry(self, text: str, image_context: Optional[str] = None) -> AIUnderstandingResult:
        if not self.api_key:
            return await self.fallback.understand_entry(text, image_context)
        # If API key exists, could call OpenAI / Gemini JSON mode, with fallback if error
        try:
            return await self.fallback.understand_entry(text, image_context)
        except Exception:
            return await self.fallback.understand_entry(text, image_context)

    async def understand_image(
        self,
        image_bytes: bytes,
        filename: str,
        caption: Optional[str] = None,
        ocr_text: Optional[str] = None
    ) -> AIUnderstandingResult:
        if not self.api_key:
            return await self.fallback.understand_image(image_bytes, filename, caption, ocr_text)
        try:
            return await self.fallback.understand_image(image_bytes, filename, caption, ocr_text)
        except Exception:
            return await self.fallback.understand_image(image_bytes, filename, caption, ocr_text)

    async def generate_diary(self, raw_input: str, entities: Dict[str, Any]) -> str:
        return await self.fallback.generate_diary(raw_input, entities)

    async def regenerate_diary(self, text: str, tone: Optional[str] = "reflective", instructions: Optional[str] = None, user_context: Optional[str] = None) -> Dict[str, str]:
        return await self.fallback.regenerate_diary(text, tone, instructions, user_context)

    async def answer_question(self, query: str, context_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        return await self.fallback.answer_question(query, context_entries)

    async def answer_question_grounded(
        self,
        system_msg: str,
        user_msg: str,
    ):
        """
        Grounded RAG: delegates to SmartLocalAIProvider deterministic fallback.
        Override this with a real API call if OPENAI_API_KEY or GEMINI_API_KEY
        points to an active model that supports chat completions.
        Returns None to trigger deterministic fallback in RAGService.
        """
        return await self.fallback.answer_question_grounded(system_msg=system_msg, user_msg=user_msg)

    async def generate_memory_story(self, entries: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        return await self.fallback.generate_memory_story(entries, title)
