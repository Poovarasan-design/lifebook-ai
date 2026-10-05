import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.ai.base import AIProvider
from app.schemas.ai import AIUnderstandingResult, ExtractedEntity, ExtractedCommitment

class SmartLocalAIProvider(AIProvider):
    async def understand_entry(self, text: str, image_context: Optional[str] = None) -> AIUnderstandingResult:
        lower = text.lower()
        
        # Extracted containers
        people = []
        places = []
        projects = []
        activities = []
        commitments = []
        tags = []
        
        # 1. Person Detection
        # Catch names following "with", "met", "saw", "called", "spoke to", "talking to", "and <Name>", "to <Name>", "for <Name>"
        detected_names = set()
        person_patterns = [
            r"\b(?:with|met|saw|called|talking to|spoke to|and|to|for)\s+([A-Z][a-z]+)\b",
            r"\b([A-Z][a-z]+)\s+and\s+I\b"
        ]
        skip_words = {
            "Today", "Yesterday", "Tomorrow", "We", "I", "The", "After", "My", "Then", 
            "Next", "Friday", "Monday", "Tuesday", "Wednesday", "Thursday", "Saturday", 
            "Sunday", "Morning", "Evening", "Night", "Home", "Work", "Office", "School",
            "Image", "Photo", "Picture", "Text", "Document", "Presentation", "Slide"
        }
        for pat in person_patterns:
            for match in re.findall(pat, text):
                if match not in skip_words:
                    detected_names.add(match)

        for name in detected_names:
            people.append(ExtractedEntity(type="person", name=name, confidence=0.95))
        
        # 2. Places Detection
        detected_places = set()
        place_matches = re.findall(r"\b(?:at|in|near|visited|visiting)\s+([A-Z][a-zA-Z\s]{2,25})\b", text)
        for p in place_matches:
            p_clean = p.strip()
            if p_clean not in skip_words and p_clean not in detected_names:
                detected_places.add(p_clean)

        for p in detected_places:
            places.append(ExtractedEntity(type="place", name=p, confidence=0.92))

        # 3. Projects Detection
        proj_matches = re.findall(r"\b([A-Z][a-zA-Z0-9_\-\s]{2,20})\s+project\b", text, re.IGNORECASE)
        for pm in proj_matches:
            proj_name = f"{pm.strip().title()} Project"
            if not any(p.name == proj_name for p in projects):
                projects.append(ExtractedEntity(type="project", name=proj_name, confidence=0.92))
            
        if "website" in lower and not any("website" in p.name.lower() for p in projects):
            projects.append(ExtractedEntity(type="project", name="Website Project", confidence=0.90))
        if "api" in lower and not any("api" in p.name.lower() for p in projects):
            projects.append(ExtractedEntity(type="project", name="API Project", confidence=0.90))
        if "app" in lower and not any("app" in p.name.lower() for p in projects):
            projects.append(ExtractedEntity(type="project", name="App Development", confidence=0.90))

        # 4. Activities Detection
        if "meeting" in lower or "discussed" in lower:
            activities.append(ExtractedEntity(type="activity", name="Meeting & Discussion", confidence=0.92))
        if "lunch" in lower or "dinner" in lower or "breakfast" in lower or "cafe" in lower:
            activities.append(ExtractedEntity(type="activity", name="Dining Out" if "restaurant" in lower or "cafe" in lower else "Meal", confidence=0.91))
        if "coding" in lower or "developed" in lower or "built" in lower or "designed" in lower:
            activities.append(ExtractedEntity(type="activity", name="Creative Sprint", confidence=0.91))
        if "travel" in lower or "trip" in lower or "flight" in lower or "train" in lower or "drive" in lower:
            activities.append(ExtractedEntity(type="activity", name="Travel & Commute", confidence=0.89))
        if "walk" in lower or "stroll" in lower or "jog" in lower or "exercise" in lower or "gym" in lower:
            activities.append(ExtractedEntity(type="activity", name="Wellness Activity", confidence=0.90))

        # 5. Commitments Detection
        from app.services.commitment_service import CommitmentService
        _, due_str, is_past_event = CommitmentService.parse_temporal_due_date(text)
        
        extracted_tasks = CommitmentService.extract_tasks_from_text(text)
        for task in extracted_tasks:
            if not any(task.lower() in c.description.lower() for c in commitments):
                proj_name = projects[0].name if projects else "Action Item"
                commitments.append(ExtractedCommitment(
                    description=task[:60].capitalize(),
                    project=proj_name,
                    due_date=due_str,
                    confidence=0.92,
                    priority="high" if "today" in due_str.lower() or "tomorrow" in due_str.lower() else "medium",
                    activity_thread=f"{proj_name} Goals",
                    next_action=task[:60].capitalize()
                ))

        # Category Determination
        category = "Personal"
        if projects or "work" in lower or "office" in lower or "code" in lower:
            category = "Work & Projects"
        elif "meeting" in lower or "client" in lower or "business" in lower:
            category = "Business"
        elif "travel" in lower or "trip" in lower or "vacation" in lower:
            category = "Travel"
        elif "beach" in lower or "relax" in lower or "park" in lower:
            category = "Leisure"

        # Tags
        tags = [category]
        if people:
            tags.extend([p.name for p in people])
        if places:
            tags.extend([p.name for p in places])

        # Draft Narrative Generation
        title = self._generate_title(text, places, projects)
        diary_draft = self._generate_polished_narrative(text, people, places, projects, commitments)

        # Tone & Mood Detection
        mood = "reflective"
        if any(w in lower for w in ["happy", "joy", "excited", "fun", "celebrat", "awesome", "great", "delighted", "smile"]):
            mood = "happy"
        elif any(w in lower for w in ["frustrat", "irritat", "headache", "stuck", "bug", "furious", "angry"]):
            mood = "frustrate"
        elif any(w in lower for w in ["annoy", "bother", "nag", "delay", "disturb"]):
            mood = "annoying"
        elif any(w in lower for w in ["boring", "bored", "dull", "tiresome", "uninteresting"]):
            mood = "boring"
        elif any(w in lower for w in ["sleepy", "tired", "exhaust", "drowsy", "fatigue", "yawn"]):
            mood = "sleepy"
        elif any(w in lower for w in ["sad", "depress", "unhappy", "cry", "lonely", "grief", "heartbroken"]):
            mood = "sad"
        elif any(w in lower for w in ["sturdy", "determined", "resilient", "strong", "firm", "disciplined", "focus", "grind"]):
            mood = "sturdy"
        elif any(w in lower for w in ["peace", "calm", "serene", "quiet", "ocean", "beach", "sunset"]):
            mood = "peaceful"
        elif any(w in lower for w in ["thank", "grateful", "blessed", "relief"]):
            mood = "grateful"

        return AIUnderstandingResult(
            title=title,
            diary_draft=diary_draft,
            category=category,
            mood=mood,
            people=people,
            places=places,
            projects=projects,
            activities=activities,
            commitments=commitments,
            tags=list(set(tags)),
            confidence=0.95,
            disambiguation=None
        )

    def _generate_title(self, text: str, places: list, projects: list) -> str:
        first_line = text.strip().split("\n")[0].split(".")[0].strip()
        if places and projects:
            return f"{projects[0].name} at {places[0].name}"
        elif places:
            return f"Reflections at {places[0].name}"
        elif projects:
            return f"Progress on {projects[0].name}"
        elif len(first_line) > 5 and len(first_line) <= 45:
            return first_line.capitalize()
        return "Daily Journal Reflection"

    def _generate_polished_narrative(self, text: str, people: list, places: list, projects: list, commitments: list) -> str:
        cleaned = text.strip()
        if not cleaned:
            return "Today was a quiet day of observation and reflection."
        if not cleaned.endswith("."):
            cleaned += "."
        if len(cleaned.split()) > 12:
            return cleaned
        return f"Taking a moment to document today: {cleaned}"

    async def generate_diary(self, raw_input: str, entities: Dict[str, Any]) -> str:
        return f"Today's memory: {raw_input}"

    async def regenerate_diary(self, text: str, tone: Optional[str] = "reflective", instructions: Optional[str] = None, user_context: Optional[str] = None) -> Dict[str, str]:
        cleaned = text.strip()
        tone_lower = (tone or "reflective").lower()
        
        if "poetic" in tone_lower:
            gen_title = "Poetic Musings"
            gen_content = f"The day slipped by in a rhythm of thoughtful moments and quiet grace. Looking back upon it now: {cleaned}"
        elif "concise" in tone_lower:
            gen_title = "Daily Summary"
            gen_content = f"{cleaned}"
        elif "detailed" in tone_lower:
            gen_title = "Detailed Journal Entry"
            gen_content = f"Documenting today in full detail: {cleaned}. Grateful for the clarity and progress made throughout the day."
        else:
            gen_title = "Reflections of Today"
            gen_content = f"Taking a quiet moment to reflect on today: {cleaned}. Grateful for the insights gained and the memories made."

        return {"title": gen_title, "content": gen_content}

    async def answer_question(self, query: str, context_entries: List[Dict[str, Any]], user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        q = query.lower()
        now_dt = datetime.now()
        current_date_str = now_dt.strftime("%A, %B %d, %Y")
        today_iso = now_dt.strftime("%Y-%m-%d")

        # 1. Today's Diary / What happened today
        if any(w in q for w in ["today", "what happened today", "read today"]):
            today_entries = [
                e for e in context_entries 
                if e.get("is_today") or today_iso in str(e.get("date", "")) or today_iso in str(e.get("entry_date", ""))
            ]
            if today_entries:
                summaries = []
                for e in today_entries[:4]:
                    desc = e.get("generated_content") or e.get("content") or e.get("raw_text") or e.get("title")
                    summaries.append(f"• {e.get('title', 'Memory')}: {desc[:140]}...")
                combined = "\n".join(summaries)
                return {
                    "answer": f"Here is what you recorded today ({current_date_str}):\n\n{combined}",
                    "source_entry_id": today_entries[0].get("id"),
                    "confidence": 0.98
                }
            return {
                "answer": f"You haven't recorded an entry for today ({current_date_str}) yet. Feel free to jot down a quick note or voice memo!",
                "source_entry_id": None,
                "confidence": 0.90
            }

        # 2. Forgetting / Commitments / Tasks
        if any(w in q for w in ["forget", "task", "commitment", "todo", "due", "deadline", "remind"]):
            commitments = (user_profile or {}).get("commitments", [])
            if commitments:
                items = []
                for c in commitments:
                    thread_info = f" [Thread: {c.get('activity_thread')}]" if c.get('activity_thread') else ""
                    action_info = f" -> Next Action: {c.get('next_action')}" if c.get('next_action') else ""
                    items.append(f"• {c.get('description')} (Project: {c.get('project', 'General')}, Due: {c.get('due_date', 'Upcoming')}{thread_info}{action_info})")
                return {
                    "answer": "Here are your active commitments and reminders:\n\n" + "\n".join(items),
                    "source_entry_id": context_entries[0]["id"] if context_entries else None,
                    "confidence": 0.98
                }
            return {
                "answer": "You currently have no pending commitments or tasks recorded in your journal.",
                "source_entry_id": None,
                "confidence": 0.95
            }

        # 3. Routines / Patterns / Habits
        if "routine" in q or "habit" in q or "pattern" in q:
            routines = (user_profile or {}).get("routines", [])
            if routines:
                r = routines[0]
                loc = f" • Location: {r.get('location')}" if r.get('location') else ""
                det = f" • Details: {r.get('details')}" if r.get('details') else ""
                return {
                    "answer": f"• Identified Routine: {r.get('title')}{loc}{det}\n• Pattern: {r.get('pattern', 'Recurring')}\n• Confidence: {int(r.get('confidence', 0.85) * 100)}%",
                    "source_entry_id": None,
                    "confidence": 0.92
                }
            return {
                "answer": "LifeBook hasn't identified any recurring routines yet. As you record more entries over time, your natural patterns and rhythms will emerge automatically.",
                "source_entry_id": None,
                "confidence": 0.90
            }

        # 4. Check query against active commitments
        commitments = (user_profile or {}).get("commitments", [])
        q_words = [w for w in q.split() if len(w) > 3 and w not in ["what", "when", "where", "which", "about", "your", "today", "show", "tell", "call"]]
        for c in commitments:
            c_text = f"{c.get('description', '')} {c.get('activity_thread', '')} {c.get('project', '')}".lower()
            if any(w in c_text for w in q_words):
                thread_info = f"\n• Activity Thread: {c.get('activity_thread')}" if c.get('activity_thread') else ""
                next_act = f"\n• Next Action: {c.get('next_action')}" if c.get('next_action') else ""
                return {
                    "answer": f"• Task: {c.get('description')}\n• Due Date: {c.get('due_date', 'Upcoming')}\n• Project: {c.get('project', 'General')}{thread_info}{next_act}\n• Status: Active Reminder Scheduled",
                    "source_entry_id": context_entries[0]["id"] if context_entries else None,
                    "confidence": 0.96
                }

        # 5. Dynamic search across all authentic memories
        if q_words and context_entries:
            best_entry = None
            best_score = 0
            for entry in context_entries:
                text = f"{entry.get('title', '')} {entry.get('content', '')} {entry.get('raw_text', '')}".lower()
                score = sum(1 for w in q_words if w in text)
                if score > best_score:
                    best_score = score
                    best_entry = entry

            if best_entry and best_score > 0:
                date_str = best_entry.get("date") or best_entry.get("entry_date") or "Recorded Entry"
                snippet = (best_entry.get("content") or best_entry.get("raw_text") or best_entry.get("title") or "")
                return {
                    "answer": f"• Found in Memory: {best_entry.get('title')} ({date_str})\n• Category: {best_entry.get('category', 'Personal')}\n• Highlight: {snippet[:200]}...",
                    "source_entry_id": best_entry.get("id"),
                    "confidence": 0.92
                }

        # 6. General answer fallback
        if context_entries:
            latest = context_entries[0]
            desc = latest.get('content') or latest.get('generated_content') or latest.get('raw_text') or ''
            return {
                "answer": f"• Latest Memory: {latest.get('title')}\n• Details: {desc[:200]}...\n• Category: {latest.get('category', 'Personal')}",
                "source_entry_id": latest.get("id"),
                "confidence": 0.85
            }
            
        return {
            "answer": "• No matching memory found in your journal for this question.",
            "source_entry_id": None,
            "confidence": 0.70
        }

    async def understand_image(
        self,
        image_bytes: bytes,
        filename: str,
        caption: Optional[str] = None,
        ocr_text: Optional[str] = None
    ) -> AIUnderstandingResult:
        """
        Multimodal image understanding for SmartLocalAIProvider.
        Extracts structured information from caption, filename, and OCR text
        without external API dependencies or hallucinations.
        """
        text_parts = []
        if caption and caption.strip():
            text_parts.append(caption.strip())
        if ocr_text and ocr_text.strip():
            text_parts.append(f"Text in Image / Document: {ocr_text.strip()}")

        combined_text = "\n".join(text_parts) if text_parts else (filename or "Visual Photo Memory")
        result = await self.understand_entry(combined_text)

        # Grounded visual title and categorization
        if not caption and not ocr_text:
            result.title = "Photo Memory"
            result.diary_draft = "Captured and saved a visual photo memory to LifeBook."
            result.category = "Visual"
        elif caption:
            result.title = caption.strip()[:60]
            if result.category == "General":
                result.category = "Visual"
        elif ocr_text and not caption:
            result.title = result.title or "Document / Image Note"
            result.diary_draft = f"Captured photo memory with readable text:\n{ocr_text[:300]}"
            if result.category == "General":
                result.category = "Documents"

        return result

    async def generate_memory_story(self, entries: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        return {
            "title": title,
            "summary": "A nostalgic look back at your milestones, connections, and projects.",
            "chapters": [
                {
                    "title": e.get("title", "Memory"),
                    "date": str(e.get("entry_date")),
                    "story": e.get("generated_content", ""),
                    "category": e.get("category", "General")
                }
                for e in entries[:5]
            ]
        }

    async def answer_question_grounded(
        self,
        system_msg: str,
        user_msg: str,
    ) -> Optional[str]:
        """
        Deterministic grounded fallback for offline/no-API mode.

        Extracts memory blocks from the context already assembled by RAGService
        and produces a structured answer without any LLM.
        NEVER fabricates facts — only uses content from supplied context.
        Supports multimodal queries (photos, documents, OCR, voice transcripts).
        """
        import re

        # Extract content between <RETRIEVED_MEMORIES> if present
        context_match = re.search(r"<RETRIEVED_MEMORIES>(.*?)</RETRIEVED_MEMORIES>", user_msg, re.DOTALL)
        context_str = context_match.group(1) if context_match else user_msg

        # Extract [Memory N] blocks from context
        mem_block_pattern = re.compile(
            r"\[Memory (\d+)\]\nEntry ID:.*?\nDate: (.*?)\nTitle: (.*?)\nCategory: (.*?)\nContent:\n(.*?)(?=\n\[Memory \d+\]|\n---|\Z)",
            re.DOTALL,
        )
        matches = mem_block_pattern.findall(context_str)

        if not matches:
            return (
                "I couldn't find a relevant memory in your LifeBook for that question."
            )

        # Extract question keywords from user_msg
        user_q_match = re.search(r"(?:<USER_QUERY>|My question:\s*)(.*?)(?:</USER_QUERY>|\nPlease|\Z)", user_msg, re.DOTALL | re.IGNORECASE)
        query_text = user_q_match.group(1).strip().lower() if user_q_match else user_msg.lower()

        is_photo_query = any(w in query_text for w in ["photo", "picture", "image", "presentation", "slide", "screenshot"])
        is_voice_query = any(w in query_text for w in ["say", "said", "voice", "audio", "recording", "spoke"])
        is_when_query = any(w in query_text for w in ["when", "last work", "what date", "timeline"])

        scored_matches = []
        for num, date, title, category, content in matches:
            score = 0
            # Clean content in case of leftover closing tags
            cleaned_content = re.sub(r"</?RETRIEVED_MEMORIES>", "", content).strip()
            content_lower = cleaned_content.lower()
            title_lower = title.lower()

            # Multimodal photo query boost
            if is_photo_query and ("photo" in content_lower or "image" in content_lower or "visual" in category.lower() or "[photo" in content_lower or "ocr" in content_lower or "slide" in content_lower):
                score += 3

            # Multimodal voice query boost
            if is_voice_query and ("voice" in content_lower or "transcript" in content_lower or "audio" in content_lower):
                score += 3

            # Keyword overlap
            q_words = [w for w in re.split(r"\W+", query_text) if len(w) > 3]
            for w in q_words:
                if w in content_lower or w in title_lower:
                    score += 1

            scored_matches.append((score, num, date, title, category, cleaned_content))

        scored_matches.sort(key=lambda x: x[0], reverse=True)

        lines = ["Here is what I found in your memories:\n"]
        for _, num, date, title, category, content in scored_matches[:3]:
            snippet = content.strip()[:250]
            if len(content.strip()) > 250:
                snippet += "..."
            lines.append(
                f"• {title.strip()} ({date.strip()}) [Memory {num}]\n"
                f"  {snippet}"
            )

        # Append Life Graph connections if present
        graph_match = re.search(r"<LIFE_GRAPH_CONNECTIONS>(.*?)</LIFE_GRAPH_CONNECTIONS>", user_msg, re.DOTALL)
        if graph_match and graph_match.group(1).strip():
            lines.append(f"\nLife Graph Connections:\n{graph_match.group(1).strip()}")

        return "\n".join(lines)


