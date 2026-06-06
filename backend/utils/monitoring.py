"""LangSmith tracing setup for backend Google ADK runs.

The LangSmith Google ADK integration traces agent invocations, tool calls, and
LLM interactions automatically after ``configure_google_adk`` is called. Runtime
enablement and destination are controlled by the standard LangSmith environment
variables, including ``LANGSMITH_TRACING``, ``LANGSMITH_API_KEY``, and
``LANGSMITH_PROJECT``.
"""

from typing import Any

from langsmith.integrations.google_adk import configure_google_adk
from utils.config import load_settings


class LangsmithMonitor:
    """Configure LangSmith's official Google ADK tracing integration."""

    _configured = False

    def __init__(
        self,
        *,
        project_name: str | None = None,
        trace_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Configure ADK tracing once before backend agents are created."""

        settings = load_settings()
        self.project_name = project_name
        self.trace_name = trace_name or settings.langsmith.backend_trace_name
        self.metadata = {"service": "backend", **(metadata or {})}
        self.tags = [*settings.langsmith.tags, "backend", *(tags or [])]
        self.enabled = self._configure()

    def _configure(self) -> bool:
        """Call LangSmith's ADK tracer configuration exactly once."""

        if self.__class__._configured:
            return True

        configured = configure_google_adk(
            name=self.trace_name,
            project_name=self.project_name,
            metadata=self.metadata,
            tags=self.tags,
        )
        self.__class__._configured = configured
        return configured

    def track_event(self, name: str, payload: dict[str, Any] | None = None) -> None:
        """Retain the route API while ADK tracing captures events automatically."""

        return None
