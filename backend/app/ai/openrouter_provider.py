import json
import logging
import httpx
from typing import Optional, Dict, Any, List
from app.ai.base import AIProvider
from app.ai.local_provider import SmartLocalAIProvider
from app.schemas.ai import (
    AIUnderstandingResult,
    ExtractedEntity,
    ExtractedCommitment
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenRouterProvider(AIProvider):
    def __init__(self):
        self.fallback = SmartLocalAIProvider()
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL or 'openai/gpt-4o-mini'
        self.base_url = 'https://openrouter.ai/api/v1/chat/completions'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost:5173',
            'X-Title': 'LifeBook AI'
        }

    async def _call_openrouter(self, messages: List[Dict[str, str]], response_format_json: bool = False, temperature: float = 0.3) -> Optional[str]:
        if not self.api_key:
            return None
        payload: Dict[str, Any] = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
        }
        if response_format_json:
            payload['response_format'] = {'type': 'json_object'}

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(self.base_url, headers=self.headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get('choices', [])
                    if choices:
                        return choices[0].get('message', {}).get('content', '')
                else:
                    logger.warning(f'OpenRouter API returned status {res.status_code}: {res.text[:200]}')
        except Exception as e:
            logger.error(f'OpenRouter call error: {e}')
        return None

    async def understand_entry(self, text: str, image_context: Optional[str] = None) -> AIUnderstandingResult:
        if not self.api_key:
            return await self.fallback.understand_entry(text, image_context)

        prompt = f'''You are an AI personal life diary parser.
Analyze this journal entry:
\"\"\"{text}\"\"\"
{f'Image context: {image_context}' if image_context else ''}

Extract the following JSON structure:
{{
  \"title\": \"Short memorable title (3-6 words)\",
  \"diary_draft\": \"Well-written, polished first-person journal narrative capturing what happened with emotional resonance\",
  \"category\": \"Category name (e.g. College / Project, Work / Business, Personal, Leisure, Travel, Food)\",
  \"mood\": \"Predicted emotional tone of the speaker from: happy, sad, frustrate, annoying, boring, sleepy, sturdy, excited, grateful, peaceful, or reflective\",
  \"people\": [ {{\"name\": \"Person Name\", \"confidence\": 0.95}} ],
  \"places\": [ {{\"name\": \"Location Name\", \"confidence\": 0.95}} ],
  \"projects\": [ {{\"name\": \"Project/Work Name\", \"confidence\": 0.95}} ],
  \"activities\": [ {{\"name\": \"Activity Name\", \"confidence\": 0.95}} ],
  \"commitments\": [
    {{
      \"description\": \"Specific action or task committed to\",
      \"project\": \"Project or context\",
      \"due_date\": \"Mentioned or inferred deadline (e.g. Tomorrow, Next Wednesday, Upcoming)\",
      \"confidence\": 0.92,
      \"priority\": \"high\"
    }}
  ],
  \"confidence\": 0.95
}}
Return ONLY valid JSON.
'''
        try:
            content = await self._call_openrouter([
                {'role': 'system', 'content': 'You are a structured diary extraction AI. Output strictly valid JSON.'},
                {'role': 'user', 'content': prompt}
            ], response_format_json=True)

            if content:
                data = json.loads(content)
                people = [ExtractedEntity(type="person", name=p.get('name', ''), confidence=p.get('confidence', 0.9)) for p in data.get('people', []) if p.get('name')]
                places = [ExtractedEntity(type="place", name=p.get('name', ''), confidence=p.get('confidence', 0.9)) for p in data.get('places', []) if p.get('name')]
                projects = [ExtractedEntity(type="project", name=p.get('name', ''), confidence=p.get('confidence', 0.9)) for p in data.get('projects', []) if p.get('name')]
                activities = [ExtractedEntity(type="activity", name=ac.get('name', ''), confidence=ac.get('confidence', 0.9)) for ac in data.get('activities', []) if ac.get('name')]
                commitments = [
                    ExtractedCommitment(
                        description=c.get('description', ''),
                        project=c.get('project', 'General'),
                        due_date=c.get('due_date', 'Upcoming'),
                        confidence=c.get('confidence', 0.9),
                        priority=c.get('priority', 'high' if 'call' in c.get('description', '').lower() or 'quotation' in c.get('description', '').lower() else 'medium'),
                        activity_thread=c.get('activity_thread'),
                        next_action=c.get('next_action')
                    ) for c in data.get('commitments', []) if c.get('description')
                ]
                tags = [data.get('category', 'Personal')]
                tags.extend([p.name for p in people])
                tags.extend([pl.name for pl in places])
                return AIUnderstandingResult(
                    title=data.get('title', 'Reflective Memory'),
                    diary_draft=data.get('diary_draft', text),
                    category=data.get('category', 'Personal'),
                    mood=data.get('mood', 'reflective'),
                    people=people,
                    places=places,
                    projects=projects,
                    activities=activities,
                    commitments=commitments,
                    tags=tags,
                    confidence=float(data.get('confidence', 0.95)),
                    disambiguation=None
                )
        except Exception as e:
            logger.warning(f'OpenRouter parsing failed, falling back to local provider: {e}')

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

        import base64
        try:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            ext = filename.split(".")[-1].lower() if "." in filename else "jpeg"
            mime_type = "image/png" if ext == "png" else "image/webp" if ext == "webp" else "image/jpeg"

            prompt = f"""You are an AI personal life diary parser analyzing an uploaded photo.
Caption provided by user: {caption or 'None'}
OCR Text detected in image: {ocr_text or 'None'}

Extract structured information without hallucinating ungrounded details.
Return strictly valid JSON with:
{{
  "title": "Memorable title (3-6 words)",
  "diary_draft": "First-person narrative describing what is in this photo",
  "category": "Visual / College / Project / Personal / Travel / Food",
  "mood": "happy, excited, reflective, grateful, or peaceful",
  "people": [ {{"name": "Person Name", "confidence": 0.95}} ],
  "places": [ {{"name": "Location Name", "confidence": 0.95}} ],
  "projects": [ {{"name": "Project Name", "confidence": 0.95}} ],
  "activities": [ {{"name": "Activity Name", "confidence": 0.95}} ],
  "commitments": [],
  "confidence": 0.95
}}"""

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}"
                            }
                        }
                    ]
                }
            ]
            content = await self._call_openrouter(messages, response_format_json=True)
            if content:
                data = json.loads(content)
                people = [ExtractedEntity(type="person", name=p.get('name', ''), confidence=p.get('confidence', 0.9)) for p in data.get('people', []) if p.get('name')]
                places = [ExtractedEntity(type="place", name=p.get('name', ''), confidence=p.get('confidence', 0.9)) for p in data.get('places', []) if p.get('name')]
                projects = [ExtractedEntity(type="project", name=p.get('name', ''), confidence=p.get('confidence', 0.9)) for p in data.get('projects', []) if p.get('name')]
                activities = [ExtractedEntity(type="activity", name=ac.get('name', ''), confidence=ac.get('confidence', 0.9)) for ac in data.get('activities', []) if ac.get('name')]
                commitments = [
                    ExtractedCommitment(
                        description=c.get('description', ''),
                        project=c.get('project', 'General'),
                        due_date=c.get('due_date', 'Upcoming'),
                        confidence=c.get('confidence', 0.9),
                        priority=c.get('priority', 'high'),
                        activity_thread=c.get('activity_thread'),
                        next_action=c.get('next_action')
                    ) for c in data.get('commitments', []) if c.get('description')
                ]
                tags = [data.get('category', 'Visual')]
                tags.extend([p.name for p in people])
                tags.extend([pl.name for pl in places])
                return AIUnderstandingResult(
                    title=data.get('title', caption or 'Photo Memory'),
                    diary_draft=data.get('diary_draft', f"Photo memory: {caption or filename}"),
                    category=data.get('category', 'Visual'),
                    mood=data.get('mood', 'reflective'),
                    people=people,
                    places=places,
                    projects=projects,
                    activities=activities,
                    commitments=commitments,
                    tags=tags,
                    confidence=float(data.get('confidence', 0.95)),
                    disambiguation=None
                )
        except Exception as e:
            logger.warning(f"OpenRouter vision understanding failed, falling back to local: {e}")

        return await self.fallback.understand_image(image_bytes, filename, caption, ocr_text)

    async def generate_diary(self, raw_input: str, entities: Dict[str, Any]) -> str:
        if not self.api_key:
            return await self.fallback.generate_diary(raw_input, entities)

        prompt = f'''Transform this raw voice or text memory into a warm, beautifully reflective first-person journal entry:
Raw input: {raw_input}
Extracted details: {json.dumps(entities)}

Return only the final diary text.'''
        content = await self._call_openrouter([
            {'role': 'system', 'content': 'You are a warm, reflective digital diary writer.'},
            {'role': 'user', 'content': prompt}
        ])
        if content:
            return content.strip()
        return await self.fallback.generate_diary(raw_input, entities)

    async def regenerate_diary(self, text: str, tone: Optional[str] = "reflective", instructions: Optional[str] = None, user_context: Optional[str] = None) -> Dict[str, str]:
        if not self.api_key:
            return await self.fallback.regenerate_diary(text, tone, instructions, user_context)

        system_msg = (
            "You are a master personal journal writer and reflective storyteller. "
            "Your task is to take the user's daily memory or draft and rewrite/regenerate it into an eloquent, "
            f"beautifully written first-person ('I') journal narrative.\n"
            f"Desired tone: {tone or 'warm and reflective'}.\n"
            + (f"User personal background: {user_context}\n" if user_context else "")
            + (f"User instructions: {instructions}\n" if instructions else "")
            + "Output strictly a valid JSON object with:\n"
            "- \"title\": An evocative, memorable 3-6 word journal title\n"
            "- \"content\": The rewritten, elevated first-person diary entry narrative"
        )
        user_msg = f"Original text or memory notes:\n\"\"\"\n{text}\n\"\"\"\n\nPlease regenerate this diary entry now."

        try:
            res_content = await self._call_openrouter([
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ], response_format_json=True, temperature=0.7)

            if res_content:
                data = json.loads(res_content)
                if data.get("content"):
                    return {
                        "title": data.get("title") or "Memories of Today",
                        "content": data.get("content")
                    }
        except Exception as e:
            logger.warning(f"OpenRouter regenerate_diary failed, using fallback: {e}")

        return await self.fallback.regenerate_diary(text, tone, instructions, user_context)

    async def answer_question(self, query: str, context_entries: List[Dict[str, Any]], user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_key:
            return await self.fallback.answer_question(query, context_entries, user_profile=user_profile)

        user_name = (user_profile or {}).get('full_name', 'User')
        profile_details = (user_profile or {}).get('preferences', {})
        commitments = (user_profile or {}).get('commitments', [])
        routines = (user_profile or {}).get('routines', [])
        entities = (user_profile or {}).get('entities', [])

        from datetime import datetime, timezone
        current_date_str = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")

        system_prompt = f'''You are LifeBook AI, the deeply personal, empathetic, and intelligent digital assistant for {user_name}.
You have direct, private access to {user_name}'s personal digital diary, commitments, habits, and life memories.

### CURRENT REFERENCE DATE (TODAY):
- Today is: {current_date_str}.

### {user_name}'s Profile & Preferences:
- Name: {user_name}
- Known background / preferences: {json.dumps(profile_details)}

### Active Commitments & Due Dates:
{json.dumps(commitments, indent=2) if commitments else 'None currently pending.'}

### Detected Routines & Habits:
{json.dumps(routines, indent=2) if routines else 'No routine records.'}

### Known People, Places & Projects (Life Graph):
{json.dumps(entities, indent=2) if entities else 'No life graph entities recorded yet.'}

### Complete Diary Memories (chronological order):
{json.dumps(context_entries, indent=2) if context_entries else 'No journal entries recorded yet.'}

Guidelines:
1. Always base your answers directly on {user_name}'s authentic memories, commitments, and profile above. Be factually accurate, thorough, and empathetic.
2. Structure your answers point by point using clear bullet points (•) for easy readability and instant comprehension, rather than dense blocks of text.
3. When asked about "today" (e.g. "What did I do today?", "Read today's diary", "Who did I meet today?"), inspect all entries for {current_date_str} and provide a bulleted summary of key moments, activities, and interactions.
4. When asked about personal preferences, tastes, or facts (e.g. "What is my favorite movie?", "What food do I like?", "What did I say about Iron Man?"), search the memory texts carefully and present the findings with clear bullet points citing relevant dates/memories.
5. When asked about specific people, places, or projects, outline the activities, discussions, dates, and next actions in bullet points based directly on the user's authentic journal entries.
6. When asked about commitments, reminders, deadlines, or "What am I forgetting?", list each item in a bullet point showing task name, project, target due date, and activity thread / next action.
7. If the question cannot be answered from any provided memory, gently state in a brief bullet that no memory has been recorded yet for that specific topic.
8. If the user writes in Tamil, Tanglish, or English, match their language style naturally while keeping point-by-point bullet formatting.
9. Speak warmly, concisely, and supportively as their personal life assistant.
'''
        try:
            content = await self._call_openrouter([
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': query}
            ], temperature=0.3)

            if content:
                # Find matching entry ID
                matched_id = None
                q_words = [w.lower() for w in query.split() if len(w) > 3 and w.lower() not in ["what", "when", "where", "which", "your", "today", "with"]]
                for e in context_entries:
                    corpus = f"{e.get('title', '')} {e.get('content', '')} {e.get('raw_text', '')}".lower()
                    if any(w in corpus for w in q_words):
                        matched_id = e.get('id')
                        break

                if not matched_id and context_entries:
                    matched_id = context_entries[0].get('id')

                return {
                    'answer': content.strip(),
                    'source_entry_id': matched_id,
                    'confidence': 0.98
                }
        except Exception as e:
            logger.warning(f'OpenRouter answer_question failed, falling back: {e}')

        return await self.fallback.answer_question(query, context_entries, user_profile=user_profile)

    async def answer_question_grounded(
        self,
        system_msg: str,
        user_msg: str,
    ):
        """
        Grounded RAG generation: uses pre-built prompt from RAGService.

        Temperature is set to 0.1 for maximum factual consistency —
        the LLM must closely follow the supplied memory context.
        Returns None on failure (RAGService will use deterministic fallback).
        """
        if not self.api_key:
            return None
        try:
            content = await self._call_openrouter(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
            )
            return content
        except Exception as e:
            logger.warning("OpenRouter answer_question_grounded failed: %s", e)
            return None

    async def generate_memory_story(self, entries: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        return await self.fallback.generate_memory_story(entries, title)
