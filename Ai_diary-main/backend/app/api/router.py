from fastapi import APIRouter
from app.api.v1 import (
    auth,
    diary,
    life_graph,
    commitments,
    routines,
    search,
    memories,
    notifications,
    users,
    admin,
    assistant
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(diary.router)
api_router.include_router(life_graph.router)
api_router.include_router(commitments.router)
api_router.include_router(routines.router)
api_router.include_router(search.router)
api_router.include_router(memories.router)
api_router.include_router(notifications.router)
api_router.include_router(users.router)
api_router.include_router(admin.router)
api_router.include_router(assistant.router)
