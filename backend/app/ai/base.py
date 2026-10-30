from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from app.schemas.ai import AIUnderstandingResult

class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, filename: str) -> Dict[str, Any]:
        pass

class AIProvider(ABC):
    @abstractmethod
    async def understand_entry(self, text: str, image_context: Optional[str] = None) -> AIUnderstandingResult:
        pass

    @abstractmethod
    async def understand_image(
        self,
        image_bytes: bytes,
        filename: str,
        caption: Optional[str] = None,
        ocr_text: Optional[str] = None
    ) -> AIUnderstandingResult:
        pass

    @abstractmethod
    async def generate_diary(self, raw_input: str, entities: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    async def regenerate_diary(self, text: str, tone: Optional[str] = "reflective", instructions: Optional[str] = None, user_context: Optional[str] = None) -> Dict[str, str]:
        pass

    @abstractmethod
    async def answer_question(self, query: str, context_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def generate_memory_story(self, entries: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        pass

    async def answer_question_grounded(
        self,
        system_msg: str,
        user_msg: str,
    ) -> Optional[str]:
        """
        Grounded RAG generation using a pre-built prompt from RAGService.

        Receives the fully assembled system prompt (with strict grounding rules
        and retrieved memories) and user message, returns the raw LLM response.

        Providers that support a chat API should override this.
        Default implementation returns None (triggers deterministic fallback).
        """
        return None
