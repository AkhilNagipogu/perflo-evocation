"""
Main FastAPI application entry point.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.init_db import init_db
from app.jobs.scheduler import shutdown_scheduler, start_scheduler

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("evocation")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager: ensures db schema/seeds, starts scheduler on startup, cleans up on shutdown."""
    logger.info("Initializing Evocation Subdomain Platform...")
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    if settings.SCHEDULER_ENABLED:
        try:
            start_scheduler()
            logger.info("Background job scheduler running")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")

    yield

    logger.info("Shutting down Evocation Subdomain Platform...")
    if settings.SCHEDULER_ENABLED:
        shutdown_scheduler()


app = FastAPI(
    title="Evocation Subdomain Rental API",
    description="Production SaaS API for automated subdomain leasing and Cloudflare DNS management.",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )


# Mount API routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Service identification endpoint."""
    return {
        "service": "Evocation Subdomain Rental API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs" if not settings.is_production else "disabled",
    }
