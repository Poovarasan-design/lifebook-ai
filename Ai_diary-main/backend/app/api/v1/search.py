from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.search import SearchQuery, ConversationalAnswer, ForgettingResponse
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.schemas.rag import RAGAnswer
from app.services.retrieval_service import retrieval_service
from app.services.rag_service import rag_service
from app.services.commitment_service import CommitmentService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_memories(
    payload: RetrievalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await retrieval_service.retrieve_memories(
        user_id=current_user.id,
        query=payload.query,
        top_k=payload.top_k,
        filters=payload.filters,
        min_score=payload.min_score,
        deduplicate=payload.deduplicate,
        db=db
    )


@router.post("", response_model=RAGAnswer)
@router.post("/ask", response_model=RAGAnswer)
async def ask_diary(
    payload: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask My Diary — Grounded RAG endpoint.

    Uses RetrievalService (Task 2) to find relevant MemoryChunks, then
    calls the LLM with a strict grounded prompt. Sources are validated
    against retrieved chunks — no fabricated citations are returned.

    Security: user_id is ALWAYS taken from the authenticated JWT token.
    Never accepts user_id from the request body.
    """
    user_name = (current_user.full_name or "").split(" ")[0] or "you"
    return await rag_service.answer_question(
        user_id=current_user.id,         # JWT-authenticated — never from payload
        query=payload.query,
        db=db,
        user_name=user_name,
    )


@router.post("/forgetting", response_model=ForgettingResponse)
def what_am_i_forgetting(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return CommitmentService.get_forgetting_commitments(current_user.id, db)
