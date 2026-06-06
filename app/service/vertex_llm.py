"""Frontend service layer for calling Vertex AI from the app."""

from typing import Any

from utils.config import load_settings


class VertexLLMClient:
    def __init__(
        self,
        project: str | None = None,
        region: str | None = None,
        backend_url: str | None = None,
    ) -> None:
        settings = load_settings()
        self.project = project or settings.vertex_ai.project
        self.region = region or settings.vertex_ai.region
        self.backend_url = backend_url or str(settings.app.backend_url)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        # Frontend may proxy through the backend; this is a lightweight stub.
        return f"[Front-end stub] Received prompt: {prompt}"
