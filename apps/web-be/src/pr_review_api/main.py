"""FastAPI application entry point.

This module creates and configures the FastAPI application instance,
including CORS middleware and route registration.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pr_review_api import __version__
from pr_review_api.config import get_settings
from pr_review_api.routers import auth, organizations


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Handles startup and shutdown events for the application.
    """
    # Startup
    yield
    # Shutdown


settings = get_settings()

app = FastAPI(
    title="PR-Review API",
    description="API for monitoring GitHub Pull Requests across organizations",
    version=__version__,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dictionary with status indicating the service is healthy.
    """
    return {"status": "ok"}


# Register routers
app.include_router(auth.router)
app.include_router(organizations.router)
