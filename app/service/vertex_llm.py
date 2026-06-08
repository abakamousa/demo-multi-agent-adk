"""Frontend service layer for calling the backend chat API."""

import json
from typing import Any
from urllib import error, request

from utils.config import load_settings


class VertexLLMClient:
    """Call the backend API from the Streamlit frontend."""

    def __init__(
        self,
        project: str | None = None,
        region: str | None = None,
        backend_url: str | None = None,
    ) -> None:
        settings = load_settings()
        self.project = project or settings.vertex_ai.project
        self.region = region or settings.vertex_ai.region
        self.backend_url = (backend_url or str(settings.app.backend_url)).rstrip("/")

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Send the prompt to the backend chat endpoint and return the answer."""

        self._ensure_backend_is_reachable()
        payload = {
            "prompt": prompt,
            "user_id": kwargs.get("user_id"),
            "context": kwargs.get("context"),
        }
        body = json.dumps(payload).encode("utf-8")
        chat_request = request.Request(
            url=f"{self.backend_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(chat_request, timeout=30) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Backend request failed with status {exc.code}: {detail}"
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(
                f"Unable to reach backend at {self.backend_url}. "
                "Make sure the FastAPI server is running."
            ) from exc

        data = json.loads(response_body)
        answer = data.get("answer")
        if not isinstance(answer, str) or not answer:
            raise RuntimeError("Backend response did not include a valid answer.")
        return answer

    def _ensure_backend_is_reachable(self) -> None:
        """Check that the backend health endpoint responds before sending chat."""

        health_request = request.Request(
            url=f"{self.backend_url}/api/health",
            method="GET",
        )

        try:
            with request.urlopen(health_request, timeout=5) as response:
                status_code = getattr(response, "status", None)
        except error.URLError as exc:
            raise RuntimeError(
                f"Backend health check failed for {self.backend_url}/api/health. "
                "Make sure the FastAPI server is running and the URL is correct."
            ) from exc

        if status_code != 200:
            raise RuntimeError(
                f"Backend health check returned status {status_code} "
                f"for {self.backend_url}/api/health."
            )
