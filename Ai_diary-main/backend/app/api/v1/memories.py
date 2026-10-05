from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import calendar
from datetime import datetime
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.diary import DiaryEntry
from app.models.commitment import Commitment
from app.schemas.diary import DiaryEntryOut

router = APIRouter(prefix="/memories", tags=["memories"])

@router.get("/on-this-day")
def on_this_day(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now()
    entries = db.query(DiaryEntry).filter(
        DiaryEntry.user_id == current_user.id
    ).order_by(DiaryEntry.entry_date.desc()).all()
    
    past_entry = None
    years_ago = 1
    # 1. Exact calendar day in a past year
    for e in entries:
        dt = e.entry_date or e.created_at
        if dt and dt.month == now.month and dt.day == now.day and dt.year < now.year:
            past_entry = e
            years_ago = now.year - dt.year
            break
            
    # 2. Or earlier past memory at least 7 days ago
    if not past_entry and entries:
        for e in entries:
            dt = e.entry_date or e.created_at
            if dt:
                entry_date_only = dt.date() if isinstance(dt, datetime) else dt
                now_date_only = now.date()
                diff_days = (now_date_only - entry_date_only).days
                if diff_days >= 7:
                    past_entry = e
                    years_ago = max(1, diff_days // 365)
                    break

    if past_entry:
        dt = past_entry.entry_date or past_entry.created_at
        formatted_date = dt.strftime("%B %d, %Y") if dt else "Earlier Memory"
        highlight = past_entry.title or (past_entry.raw_text[:80] + "..." if past_entry.raw_text else "A memorable day in your journal.")
        return {
            "has_memory": True,
            "years_ago": years_ago,
            "date": formatted_date,
            "entry": DiaryEntryOut.model_validate(past_entry),
            "highlight": highlight
        }
    return {"has_memory": False}

@router.get("/calendar")
def get_calendar_activities(
    year: int = Query(2026, ge=2020, le=2030),
    month: int = Query(9, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Fetch user's diary entries
    entries = db.query(DiaryEntry).filter(
        DiaryEntry.user_id == current_user.id
    ).all()

    # 2. Fetch user's commitments
    commitments = db.query(Commitment).filter(
        Commitment.user_id == current_user.id
    ).all()

    # Calculate month days
    num_days = calendar.monthrange(year, month)[1]
    month_name = datetime(year, month, 1).strftime("%B")
    first_weekday = calendar.monthrange(year, month)[0]  # 0=Monday, 6=Sunday
    
    def get_entry_dt(e):
        return e.entry_date or e.created_at

    def get_commitment_dt(c):
        return c.resolved_due_date or c.created_at

    days_data = []
    
    for d in range(1, num_days + 1):
        day_date = f"{year:04d}-{month:02d}-{d:02d}"
        
        # Match entries
        day_entries = [
            e for e in entries
            if get_entry_dt(e) and get_entry_dt(e).year == year and get_entry_dt(e).month == month and get_entry_dt(e).day == d
        ]
        
        # Match commitments
        day_commitments = [
            c for c in commitments
            if (get_commitment_dt(c) and get_commitment_dt(c).year == year and get_commitment_dt(c).month == month and get_commitment_dt(c).day == d)
            or (c.diary_entry_id in [e.id for e in day_entries])
        ]
        
        # Dominant mood
        dominant_mood = day_entries[0].mood if day_entries and day_entries[0].mood else None
        
        # Special badges
        is_special = False
        special_badge = None
        for e in day_entries:
            t_lower = (e.title or "").lower() + " " + (e.raw_text or "").lower()
            if "hackathon" in t_lower or "sprint" in t_lower:
                is_special = True
                special_badge = "Project Sprint"
            elif "portrait" in t_lower or "art" in t_lower or "sketch" in t_lower:
                is_special = True
                special_badge = "Creative Flow"
            elif "client" in t_lower or "meeting" in t_lower or "quotation" in t_lower:
                is_special = True
                special_badge = "Client Milestone"
            elif "beach" in t_lower or "nature" in t_lower or "park" in t_lower:
                is_special = True
                special_badge = "Rest & Reflection"
            elif e.photo_urls and len(e.photo_urls) > 0:
                is_special = True
                special_badge = "Photo Memory"

        days_data.append({
            "date": day_date,
            "day": d,
            "has_entry": len(day_entries) > 0,
            "entries_count": len(day_entries),
            "dominant_mood": dominant_mood,
            "is_special": is_special,
            "special_badge": special_badge,
            "entries": [
                {
                    "id": e.id,
                    "title": e.title or "Daily Memory",
                    "category": e.category or "General",
                    "mood": e.mood,
                    "generated_content": e.generated_content or e.raw_text,
                    "raw_text": e.raw_text,
                    "photo_urls": e.photo_urls or [],
                    "entry_date": get_entry_dt(e).strftime("%B %d, %Y") if get_entry_dt(e) else day_date
                }
                for e in day_entries
            ],
            "commitments_count": len(day_commitments),
            "commitments": [
                {
                    "id": c.id,
                    "description": c.description,
                    "project": c.project,
                    "status": c.status,
                    "due_date": c.due_date,
                    "priority": c.priority,
                    "activity_thread": getattr(c, "activity_thread", None),
                    "next_action": getattr(c, "next_action", None)
                }
                for c in day_commitments
            ]
        })

    # Curated Monthly Specials from user entries
    month_entries = [e for e in entries if get_entry_dt(e) and get_entry_dt(e).year == year and get_entry_dt(e).month == month]
    monthly_specials = []
    for e in month_entries:
        t_lower = (e.title or "").lower()
        badge = "Special Moment"
        if "milestone" in t_lower or "achieved" in t_lower or "finish" in t_lower:
            badge = "⭐ Milestone Achievement"
        elif "creative" in t_lower or "art" in t_lower or "design" in t_lower:
            badge = "🎨 Creative Flow"
        elif "meeting" in t_lower or "client" in t_lower or "project" in t_lower:
            badge = "💼 Work & Collaboration"
        elif "travel" in t_lower or "trip" in t_lower or "visit" in t_lower:
            badge = "✈️ Journey & Exploration"
        elif "peaceful" in t_lower or "reflect" in t_lower or "relax" in t_lower:
            badge = "🌊 Soulful Reflections"
            
        people_names = [ent.name for ent in e.entities if ent.type == "person"] if hasattr(e, "entities") and e.entities else []
        if not people_names:
            people_names = ["Self"]

        monthly_specials.append({
            "id": e.id,
            "title": e.title or "Memorable Day",
            "date": e.entry_date.strftime("%B %d, %Y") if e.entry_date else f"{month_name} {year}",
            "badge": badge,
            "summary": (e.generated_content or e.raw_text or "")[:200] + ("..." if len(e.generated_content or e.raw_text or "") > 200 else ""),
            "photo_url": (e.photo_urls[0] if e.photo_urls else None),
            "category": e.category or "Personal",
            "mood": e.mood or "fulfilled",
            "people": people_names
        })

    # Curated Yearly Specials based on selected year & user entries
    year_entries = [e for e in entries if get_entry_dt(e) and get_entry_dt(e).year == year]
    yearly_specials = []

    for e in year_entries:
        t_lower = (e.title or "").lower() + " " + (e.raw_text or "").lower()
        badge = "🏆 Year Milestone"
        if "milestone" in t_lower or "project" in t_lower:
            badge = "🏆 Major Milestone"
        elif "art" in t_lower or "creative" in t_lower:
            badge = "🎨 Creative Breakthrough"
        elif "trip" in t_lower or "travel" in t_lower or "explore" in t_lower:
            badge = "✈️ Journey Highlight"
        elif "friend" in t_lower or "family" in t_lower or "reunion" in t_lower:
            badge = "❤️ Cherished Connections"

        people_names = [ent.name for ent in e.entities if ent.type == "person"] if hasattr(e, "entities") and e.entities else []
        if not people_names:
            people_names = ["Self"]

        yearly_specials.append({
            "id": f"entry-year-{e.id}",
            "title": e.title or "Annual Highlight",
            "date": get_entry_dt(e).strftime("%B %d, %Y") if get_entry_dt(e) else f"{year}",
            "badge": badge,
            "summary": (e.generated_content or e.raw_text or "")[:220] + ("..." if len(e.generated_content or e.raw_text or "") > 220 else ""),
            "photo_url": (e.photo_urls[0] if e.photo_urls else None),
            "category": e.category or "Personal",
            "mood": e.mood or "inspired",
            "people": people_names
        })

    if len(year_entries) > 0:
        annual_story = f"{year} has been a personal journey documented with {len(year_entries)} memories across your life journal. Every reflection, project, and meaningful encounter captured here contributes to a life richly remembered."
    else:
        annual_story = f"No memories have been recorded for {year} yet. Use LifeBook to log your thoughts, voice notes, and daily moments to build your personal life story."

    return {
        "year": year,
        "month": month,
        "month_name": month_name,
        "first_weekday": first_weekday,
        "days": days_data,
        "monthly_specials": monthly_specials,
        "yearly_specials": yearly_specials,
        "annual_story": annual_story
    }
