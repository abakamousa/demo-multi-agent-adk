"""Langfuse tracing helpers for frontend-local workflows."""

from typing import Any

from langfuse import Langfuse

from utils.config import load_settings


class LangfuseMonitor:
    """Provide a Langfuse client wrapper for frontend instrumentation."""

    def __init__(
        self,
        *,
        trace_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Initialize frontend tracing defaults from validated config."""

        settings = load_settings()
        self._client: Any | None = None
        self.langfuse_config = settings.langfuse
        self.trace_name = trace_name or settings.langfuse.frontend_trace_name
        self.metadata = {"service": "frontend", **(metadata or {})}
        self.tags = [*settings.langfuse.tags, "frontend", *(tags or [])]

    def track_event(self, name: str, payload: dict[str, Any] | None = None) -> None:
        """Keep the app API stable; backend ADK calls carry detailed traces."""

        return None

    def flush(self) -> None:
        """Flush queued Langfuse events for short-lived frontend scripts."""

        self.client.flush()

    @property
    def client(self) -> Any:
        """Return the Langfuse client, creating it on first tracing use."""

        if self._client is None:
            self._client = Langfuse(
                public_key=(
                    self.langfuse_config.public_key.get_secret_value()
                    if self.langfuse_config.public_key
                    else None
                ),
                secret_key=(
                    self.langfuse_config.secret_key.get_secret_value()
                    if self.langfuse_config.secret_key
                    else None
                ),
                base_url=str(self.langfuse_config.base_url),
            )
        return self._client
