"""Backend FastAPI application entrypoint."""

from fastapi import FastAPI

from backend.api.routes import router
from utils.config import load_settings

settings = load_settings()

app = FastAPI(
    title=settings.backend.title,
    description=settings.backend.description,
    version=settings.backend.version,
)
app.include_router(router, prefix="/api")


@app.get("/healthz")
def health_check() -> dict[str, str]:
    """Return a lightweight readiness response for health checks."""

    return {"status": "ok"}
