"""LangSmith tracing setup for frontend-side Google ADK usage.

The frontend currently calls the backend service, but this wrapper uses the same
official LangSmith Google ADK integration so any future local ADK agent runs are
traced consistently. Configure LangSmith with ``LANGSMITH_TRACING``,
``LANGSMITH_API_KEY``, and ``LANGSMITH_PROJECT`` in the environment.
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
        """Configure ADK tracing once for frontend-local agent runs."""

        settings = load_settings()
        self.project_name = project_name
        self.trace_name = trace_name or settings.langsmith.frontend_trace_name
        self.metadata = {"service": "frontend", **(metadata or {})}
        self.tags = [*settings.langsmith.tags, "frontend", *(tags or [])]
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
        """Retain the app API while ADK tracing captures events automatically."""

        return None
