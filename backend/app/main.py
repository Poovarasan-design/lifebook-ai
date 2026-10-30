import os
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
import app.models  # Ensure all models are registered
from app.api.router import api_router
from app.api.v1.auth import router as auth_router
from app.core.security_middleware import (
    SecurityHeadersMiddleware,
    RateLimiterMiddleware,
    SafeLoggingMiddleware
)

logger = logging.getLogger("app.main")

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Ensure storage directory exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 1. Add Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. Add Safe Request Logging Middleware
app.add_middleware(SafeLoggingMiddleware)

# 3. Add Rate Limiter Middleware
app.add_middleware(RateLimiterMiddleware, max_requests_per_minute=400)

# 4. Set CORS enabled origins
origins = settings.CORS_ORIGINS if settings.ENVIRONMENT == "production" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 router (/api/v1/...)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include direct /api/auth router for standards compatibility (/api/auth/...)
app.include_router(auth_router, prefix="/api")


# Health and Readiness Endpoints
@app.get("/health")
@app.get("/api/health")
def health_check():
    """Liveness probe: verifies server process is responsive."""
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "ai_provider": settings.AI_PROVIDER
    }


@app.get("/health/ready")
@app.get("/api/health/ready")
def readiness_check():
    """Readiness probe: verifies database connection and storage availability."""
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception as exc:
        logger.error(f"Readiness check failed DB connection: {exc}")

    storage_ok = os.path.exists(settings.STORAGE_DIR) and os.access(settings.STORAGE_DIR, os.W_OK)

    if db_ok and storage_ok:
        return {
            "status": "ready",
            "database": "connected",
            "storage": "writable"
        }
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "unavailable",
            "database": "connected" if db_ok else "disconnected",
            "storage": "writable" if storage_ok else "unwritable"
        }
    )
