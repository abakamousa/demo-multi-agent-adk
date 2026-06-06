"""Langfuse tracing helpers for backend Google ADK runs.

Langfuse does not require a Google ADK-specific patcher for this app. The
backend wraps each ADK runner call in an explicit agent observation, propagates
user and session attributes, and records request input plus final output.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from langfuse import Langfuse, propagate_attributes

from utils.config import load_settings

MAX_METADATA_VALUE_LENGTH = 200


class LangfuseMonitor:
    """Create Langfuse observations for backend agent workflows."""

    def __init__(
        self,
        *,
        trace_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Initialize the Langfuse client and trace defaults."""

        settings = load_settings()
        self._client: Any | None = None
        self.langfuse_config = settings.langfuse
        self.trace_name = trace_name or settings.langfuse.backend_trace_name
        self.metadata = self._metadata(
            {
                "service": "backend",
                "adk_app": settings.adk.app_name,
                "model": settings.adk.model_name,
                "region": settings.vertex_ai.region,
                **(metadata or {}),
            }
        )
        self.tags = [*settings.langfuse.tags, "backend", *(tags or [])]

    @contextmanager
    def trace_agent_run(
        self,
        *,
        prompt: str,
        user_id: str,
        session_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """Trace one ADK agent request with user and session context."""

        merged_metadata = self._metadata({**self.metadata, **(metadata or {})})
        with self.client.start_as_current_observation(
            as_type="agent",
            name=self.trace_name,
            input={"prompt": prompt},
            metadata=merged_metadata,
        ) as span:
            with propagate_attributes(
                user_id=user_id,
                session_id=session_id,
                tags=self.tags,
                metadata=merged_metadata,
            ):
                yield span

    def track_event(self, name: str, payload: dict[str, Any] | None = None) -> None:
        """Retain route compatibility; request tracing happens in the service."""

        return None

    def flush(self) -> None:
        """Flush queued Langfuse events for short-lived commands and tests."""

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

    def _metadata(self, values: dict[str, Any]) -> dict[str, str]:
        """Convert metadata values to Langfuse-safe short strings."""

        metadata = {}
        for key, value in values.items():
            normalized_key = "".join(
                character for character in key if character.isalnum()
            )
            if not normalized_key or value is None:
                continue
            metadata[normalized_key] = str(value)[:MAX_METADATA_VALUE_LENGTH]
        return metadata
