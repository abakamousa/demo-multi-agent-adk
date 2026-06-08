"""Backend FastAPI application entrypoint."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from utils.config import load_settings

settings = load_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.backend.title,
    description=settings.backend.description,
    version=settings.backend.version,
)

if settings.backend.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router, prefix="/api")


@app.get("/healthz")
@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Return a lightweight readiness response for health checks."""

    return {"status": "ok"}


@app.on_event("startup")
async def log_backend_configuration() -> None:
    """Log the active auth mode so config issues are visible at startup."""

    auth_mode = (
        "gemini_api_key" if settings.vertex_ai.google_api_key else "vertex_or_missing"
    )
    logger.info(
        "Backend startup config: project=%s region=%s auth_mode=%s has_google_api_key=%s",
        settings.vertex_ai.project,
        settings.vertex_ai.region,
        auth_mode,
        settings.vertex_ai.google_api_key is not None,
    )
