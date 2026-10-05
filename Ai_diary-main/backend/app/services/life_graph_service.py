from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.diary import DiaryEntry
from app.models.entity import Entity
from app.models.commitment import Commitment
from app.models.life_graph import LifeGraphRelationship
from app.schemas.graph import (
    LifeGraphOut, GraphNode, GraphEdge,
    EntityHistoryOut, EntityTimelineItem,
    EntityCommitmentSummary, EntityRelationshipItem,
    EntityConflictItem
)

class LifeGraphService:
    """
    Advanced Life Graph Service for Phase 6.
    Provides graph synthesis, deduplication, timeline-ordered entity history,
    conflict detection, and graph-assisted RAG retrieval context.
    """

    @staticmethod
    def sync_entry_to_graph(entry: DiaryEntry, db: Session):
        from app.services.memory_intelligence_service import memory_intelligence_service
        memory_intelligence_service.sync_entry_to_graph_deduped(entry, db)

    @staticmethod
    def get_user_graph(user_id: str, db: Session) -> LifeGraphOut:
        """
        Retrieves the complete graph for the authenticated user, deduplicating nodes and edges.
        """
        rels = db.query(LifeGraphRelationship).filter(
            LifeGraphRelationship.user_id == user_id
        ).all()
        
        nodes_map: Dict[str, GraphNode] = {}
        edges: List[GraphEdge] = []
        
        # Add root user node
        nodes_map["You"] = GraphNode(id="You", label="You", type="User", attributes={"role": "Self"})

        for r in rels:
            s_name = (r.source_name or "").strip()
            t_name = (r.target_name or "").strip()
            if not s_name or not t_name:
                continue

            if s_name not in nodes_map:
                nodes_map[s_name] = GraphNode(
                    id=s_name,
                    label=s_name,
                    type=r.source_type,
                    attributes={"count": 1}
                )
            else:
                nodes_map[s_name].attributes["count"] = nodes_map[s_name].attributes.get("count", 0) + 1

            if t_name not in nodes_map:
                nodes_map[t_name] = GraphNode(
                    id=t_name,
                    label=t_name,
                    type=r.target_type,
                    attributes={"count": 1}
                )
            else:
                nodes_map[t_name].attributes["count"] = nodes_map[t_name].attributes.get("count", 0) + 1

            edges.append(GraphEdge(
                id=r.id,
                source=s_name,
                target=t_name,
                label=r.relationship_type,
                confidence=r.confidence or 0.95
            ))

        return LifeGraphOut(nodes=list(nodes_map.values()), edges=edges)

    @staticmethod
    def get_user_entities(user_id: str, db: Session) -> Dict[str, Any]:
        """
        Lists all summarized entities (people, places, projects) for the user.
        """
        entities = db.query(Entity).filter(Entity.user_id == user_id).all()
        
        people_dict: Dict[str, Dict[str, Any]] = {}
        places_dict: Dict[str, Dict[str, Any]] = {}
        projects_dict: Dict[str, Dict[str, Any]] = {}
        
        for e in entities:
            entry = e.entry
            entry_info = None
            if entry:
                entry_info = {
                    "id": entry.id,
                    "title": entry.title or "Memory",
                    "date": entry.entry_date.strftime("%B %d, %Y") if entry.entry_date else "",
                    "photos": entry.photo_urls or []
                }
                
            if e.type == "person":
                if e.name not in people_dict:
                    people_dict[e.name] = {
                        "name": e.name,
                        "type": "person",
                        "count": 0,
                        "last_seen": entry_info["date"] if entry_info else "Recently",
                        "memories": [],
                        "relationships": ["Friend", "Collaborator"]
                    }
                people_dict[e.name]["count"] += 1
                if entry_info and not any(m["id"] == entry_info["id"] for m in people_dict[e.name]["memories"]):
                    people_dict[e.name]["memories"].append(entry_info)
                    
            elif e.type == "place":
                if e.name not in places_dict:
                    places_dict[e.name] = {
                        "name": e.name,
                        "type": "place",
                        "count": 0,
                        "last_visited": entry_info["date"] if entry_info else "Recently",
                        "memories": [],
                        "photos": []
                    }
                places_dict[e.name]["count"] += 1
                if entry_info and not any(m["id"] == entry_info["id"] for m in places_dict[e.name]["memories"]):
                    places_dict[e.name]["memories"].append(entry_info)
                    if entry_info["photos"]:
                        places_dict[e.name]["photos"].extend(entry_info["photos"])

            elif e.type == "project":
                if e.name not in projects_dict:
                    projects_dict[e.name] = {
                        "name": e.name,
                        "type": "project",
                        "count": 0,
                        "last_updated": entry_info["date"] if entry_info else "Recently",
                        "memories": []
                    }
                projects_dict[e.name]["count"] += 1
                if entry_info and not any(m["id"] == entry_info["id"] for m in projects_dict[e.name]["memories"]):
                    projects_dict[e.name]["memories"].append(entry_info)

        return {
            "people": list(people_dict.values()),
            "places": list(places_dict.values()),
            "projects": list(projects_dict.values())
        }

    # -----------------------------------------------------------------------
    # TIMELINE & ENTITY HISTORY QUERIES (PERSON, PROJECT, PLACE)
    # -----------------------------------------------------------------------

    @staticmethod
    def get_person_history(user_id: str, person_name: str, db: Session) -> EntityHistoryOut:
        """
        Returns full timeline, associated projects, places, commitments, and conflict signals for a Person.
        """
        clean_name = person_name.strip()
        
        # 1. Fetch entries mentioning this person
        entities = db.query(Entity).filter(
            Entity.user_id == user_id,
            Entity.type == "person",
            Entity.name.ilike(clean_name)
        ).all()

        entry_ids = [e.diary_entry_id for e in entities if e.diary_entry_id]
        entries = db.query(DiaryEntry).filter(
            DiaryEntry.user_id == user_id,
            DiaryEntry.id.in_(entry_ids)
        ).order_by(DiaryEntry.entry_date.asc()).all()

        timeline = [
            EntityTimelineItem(
                entry_id=entry.id,
                date=entry.entry_date.strftime("%B %d, %Y") if entry.entry_date else None,
                title=entry.title or "Memory",
                snippet=(entry.generated_content or entry.raw_text or "")[:200],
                category=entry.category,
                photos=entry.photo_urls or [],
                relation="met / collaborated"
            )
            for entry in entries
        ]

        # 2. Fetch graph relationships for this person
        rels = db.query(LifeGraphRelationship).filter(
            LifeGraphRelationship.user_id == user_id,
            or_(
                LifeGraphRelationship.source_name.ilike(clean_name),
                LifeGraphRelationship.target_name.ilike(clean_name)
            )
        ).all()

        relationships: List[EntityRelationshipItem] = []
        related_entities: Dict[str, List[str]] = {"projects": [], "places": [], "activities": []}
        seen_rels = set()

        for r in rels:
            is_source = r.source_name.lower() == clean_name.lower()
            other_name = r.target_name if is_source else r.source_name
            other_type = r.target_type if is_source else r.source_type
            rel_label = r.relationship_type

            rel_key = (other_name, other_type, rel_label)
            if rel_key not in seen_rels and other_name.lower() != "you":
                seen_rels.add(rel_key)
                relationships.append(EntityRelationshipItem(
                    target_name=other_name,
                    target_type=other_type,
                    relationship=rel_label,
                    confidence=r.confidence or 0.95
                ))
                if other_type.lower() == "project" and other_name not in related_entities["projects"]:
                    related_entities["projects"].append(other_name)
                elif other_type.lower() == "place" and other_name not in related_entities["places"]:
                    related_entities["places"].append(other_name)
                elif other_type.lower() == "activity" and other_name not in related_entities["activities"]:
                    related_entities["activities"].append(other_name)

        # 3. Commitments involving this person or linked entries
        comms = db.query(Commitment).filter(
            Commitment.user_id == user_id,
            or_(
                Commitment.diary_entry_id.in_(entry_ids),
                Commitment.description.ilike(f"%{clean_name}%")
            )
        ).all()

        commitments_summary = [
            EntityCommitmentSummary(
                id=c.id,
                description=c.description,
                status=c.status,
                due_date=c.due_date,
                priority=c.priority
            )
            for c in comms
        ]

        # 4. Conflict & stale relationship detection
        conflicts: List[EntityConflictItem] = []
        now = datetime.now(timezone.utc)
        if entries:
            last_entry = entries[-1]
            if last_entry.entry_date:
                dt = last_entry.entry_date if last_entry.entry_date.tzinfo else last_entry.entry_date.replace(tzinfo=timezone.utc)
                if (now - dt).days > 180:
                    conflicts.append(EntityConflictItem(
                        issue_type="stale_connection",
                        description=f"No recorded interactions with {clean_name} for over {(now - dt).days} days.",
                        severity="low"
                    ))

        return EntityHistoryOut(
            name=clean_name,
            type="person",
            count=len(entries),
            first_seen=entries[0].entry_date.strftime("%B %d, %Y") if entries and entries[0].entry_date else None,
            last_seen=entries[-1].entry_date.strftime("%B %d, %Y") if entries and entries[-1].entry_date else None,
            timeline=timeline,
            related_entities=related_entities,
            commitments=commitments_summary,
            relationships=relationships,
            conflicts=conflicts
        )

    @staticmethod
    def get_project_history(user_id: str, project_name: str, db: Session) -> EntityHistoryOut:
        """
        Returns full history, collaborators, commitments, and status timeline for a Project.
        """
        clean_name = project_name.strip()

        # 1. Fetch entries mentioning or tied to this project
        entities = db.query(Entity).filter(
            Entity.user_id == user_id,
            Entity.type == "project",
            Entity.name.ilike(clean_name)
        ).all()
        entry_ids = [e.diary_entry_id for e in entities if e.diary_entry_id]

        entries = db.query(DiaryEntry).filter(
            DiaryEntry.user_id == user_id,
            or_(
                DiaryEntry.id.in_(entry_ids),
                DiaryEntry.title.ilike(f"%{clean_name}%"),
                DiaryEntry.raw_text.ilike(f"%{clean_name}%")
            )
        ).order_by(DiaryEntry.entry_date.asc()).all()

        timeline = [
            EntityTimelineItem(
                entry_id=entry.id,
                date=entry.entry_date.strftime("%B %d, %Y") if entry.entry_date else None,
                title=entry.title or "Memory",
                snippet=(entry.generated_content or entry.raw_text or "")[:200],
                category=entry.category,
                photos=entry.photo_urls or [],
                relation="worked_on"
            )
            for entry in entries
        ]

        # 2. Fetch project commitments
        comms = db.query(Commitment).filter(
            Commitment.user_id == user_id,
            Commitment.project.ilike(clean_name)
        ).all()

        commitments_summary = [
            EntityCommitmentSummary(
                id=c.id,
                description=c.description,
                status=c.status,
                due_date=c.due_date,
                priority=c.priority
            )
            for c in comms
        ]

        # 3. Graph relationships (Collaborators, places)
        rels = db.query(LifeGraphRelationship).filter(
            LifeGraphRelationship.user_id == user_id,
            or_(
                LifeGraphRelationship.source_name.ilike(clean_name),
                LifeGraphRelationship.target_name.ilike(clean_name)
            )
        ).all()

        relationships: List[EntityRelationshipItem] = []
        related_entities: Dict[str, List[str]] = {"people": [], "places": [], "commitments": []}
        seen_rels = set()

        for r in rels:
            is_source = r.source_name.lower() == clean_name.lower()
            other_name = r.target_name if is_source else r.source_name
            other_type = r.target_type if is_source else r.source_type
            rel_label = r.relationship_type

            rel_key = (other_name, other_type, rel_label)
            if rel_key not in seen_rels and other_name.lower() != "you":
                seen_rels.add(rel_key)
                relationships.append(EntityRelationshipItem(
                    target_name=other_name,
                    target_type=other_type,
                    relationship=rel_label,
                    confidence=r.confidence or 0.95
                ))
                if other_type.lower() == "person" and other_name not in related_entities["people"]:
                    related_entities["people"].append(other_name)
                elif other_type.lower() == "place" and other_name not in related_entities["places"]:
                    related_entities["places"].append(other_name)

        # 4. Conflicts (e.g. overdue commitments)
        conflicts: List[EntityConflictItem] = []
        overdue = [c for c in comms if c.status == "PENDING" and c.resolved_due_date and (c.resolved_due_date.replace(tzinfo=timezone.utc) if c.resolved_due_date.tzinfo is None else c.resolved_due_date) < datetime.now(timezone.utc)]
        if overdue:
            conflicts.append(EntityConflictItem(
                issue_type="overdue_commitments",
                description=f"Project has {len(overdue)} overdue pending commitments.",
                severity="medium"
            ))

        return EntityHistoryOut(
            name=clean_name,
            type="project",
            count=len(entries),
            first_seen=entries[0].entry_date.strftime("%B %d, %Y") if entries and entries[0].entry_date else None,
            last_seen=entries[-1].entry_date.strftime("%B %d, %Y") if entries and entries[-1].entry_date else None,
            timeline=timeline,
            related_entities=related_entities,
            commitments=commitments_summary,
            relationships=relationships,
            conflicts=conflicts
        )

    @staticmethod
    def get_place_history(user_id: str, place_name: str, db: Session) -> EntityHistoryOut:
        """
        Returns full history, activities, co-visitors, and photos associated with a Place.
        """
        clean_name = place_name.strip()

        # 1. Fetch entries featuring this place
        entities = db.query(Entity).filter(
            Entity.user_id == user_id,
            Entity.type == "place",
            Entity.name.ilike(clean_name)
        ).all()
        entry_ids = [e.diary_entry_id for e in entities if e.diary_entry_id]

        entries = db.query(DiaryEntry).filter(
            DiaryEntry.user_id == user_id,
            or_(
                DiaryEntry.id.in_(entry_ids),
                DiaryEntry.raw_text.ilike(f"%{clean_name}%")
            )
        ).order_by(DiaryEntry.entry_date.asc()).all()

        timeline = [
            EntityTimelineItem(
                entry_id=entry.id,
                date=entry.entry_date.strftime("%B %d, %Y") if entry.entry_date else None,
                title=entry.title or "Memory",
                snippet=(entry.generated_content or entry.raw_text or "")[:200],
                category=entry.category,
                photos=entry.photo_urls or [],
                relation="visited / hosted"
            )
            for entry in entries
        ]

        # 2. Graph relationships
        rels = db.query(LifeGraphRelationship).filter(
            LifeGraphRelationship.user_id == user_id,
            or_(
                LifeGraphRelationship.source_name.ilike(clean_name),
                LifeGraphRelationship.target_name.ilike(clean_name)
            )
        ).all()

        relationships: List[EntityRelationshipItem] = []
        related_entities: Dict[str, List[str]] = {"people": [], "activities": [], "projects": []}
        seen_rels = set()

        for r in rels:
            is_source = r.source_name.lower() == clean_name.lower()
            other_name = r.target_name if is_source else r.source_name
            other_type = r.target_type if is_source else r.source_type
            rel_label = r.relationship_type

            rel_key = (other_name, other_type, rel_label)
            if rel_key not in seen_rels and other_name.lower() != "you":
                seen_rels.add(rel_key)
                relationships.append(EntityRelationshipItem(
                    target_name=other_name,
                    target_type=other_type,
                    relationship=rel_label,
                    confidence=r.confidence or 0.95
                ))
                if other_type.lower() == "person" and other_name not in related_entities["people"]:
                    related_entities["people"].append(other_name)
                elif other_type.lower() == "activity" and other_name not in related_entities["activities"]:
                    related_entities["activities"].append(other_name)
                elif other_type.lower() == "project" and other_name not in related_entities["projects"]:
                    related_entities["projects"].append(other_name)

        return EntityHistoryOut(
            name=clean_name,
            type="place",
            count=len(entries),
            first_seen=entries[0].entry_date.strftime("%B %d, %Y") if entries and entries[0].entry_date else None,
            last_seen=entries[-1].entry_date.strftime("%B %d, %Y") if entries and entries[-1].entry_date else None,
            timeline=timeline,
            related_entities=related_entities,
            commitments=[],
            relationships=relationships,
            conflicts=[]
        )

    @staticmethod
    def get_entity_history(user_id: str, entity_type: str, entity_name: str, db: Session) -> EntityHistoryOut:
        """
        Unified router for any entity history query.
        """
        e_type = (entity_type or "").lower().strip()
        if e_type == "person":
            return LifeGraphService.get_person_history(user_id, entity_name, db)
        elif e_type == "project":
            return LifeGraphService.get_project_history(user_id, entity_name, db)
        elif e_type == "place":
            return LifeGraphService.get_place_history(user_id, entity_name, db)
        else:
            return LifeGraphService.get_person_history(user_id, entity_name, db)

    # -----------------------------------------------------------------------
    # GRAPH-AUGMENTED RAG RETRIEVAL CONTEXT
    # -----------------------------------------------------------------------

    @staticmethod
    def get_graph_context_for_rag(user_id: str, query: str, db: Session) -> str:
        """
        Extracts relevant structural graph connections for entities mentioned in the query
        or retrieved memories, providing grounded cross-entity relationships for RAG.
        Strictly user-scoped and grounded.
        """
        if not user_id or not query:
            return ""

        # Fetch user relationships
        rels = db.query(LifeGraphRelationship).filter(
            LifeGraphRelationship.user_id == user_id
        ).all()

        if not rels:
            return ""

        matched_connections: List[str] = []
        seen = set()
        query_lower = query.lower()

        for r in rels:
            s_name = (r.source_name or "").strip()
            t_name = (r.target_name or "").strip()
            if s_name.lower() == "you":
                continue

            # Check if source or target appears in query
            if s_name.lower() in query_lower or t_name.lower() in query_lower:
                conn_key = (s_name, r.relationship_type, t_name)
                if conn_key not in seen:
                    seen.add(conn_key)
                    matched_connections.append(
                        f"• {r.source_type} '{s_name}' {r.relationship_type} {r.target_type} '{t_name}'"
                    )

        if matched_connections:
            return "\n".join(matched_connections[:6])
        return ""

life_graph_service = LifeGraphService()
