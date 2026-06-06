"""Service layer for running the ADK root agent on Vertex AI/Gemini."""

import asyncio
import inspect
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from backend.agents.orchestrator import create_root_agent
from utils.config import load_settings


class VertexLLMService:
    """Run the backend's ADK root agent behind a simple service interface."""

    def __init__(
        self,
        project: str | None = None,
        region: str | None = None,
        model_name: str | None = None,
    ) -> None:
        settings = load_settings()
        self.project = project or settings.vertex_ai.project
        self.region = region or settings.vertex_ai.region
        self.model_name = model_name or settings.adk.model_name
        self.app_name = settings.adk.app_name
        self.default_user_id = settings.adk.default_user_id
        self._runner: Any | None = None
        self._session_service: Any | None = None

    async def generate_async(
        self,
        prompt: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Run the ADK root agent and return its final text response."""

        runner = self._get_runner()
        session_service = self._session_service
        resolved_user_id = user_id or self.default_user_id
        resolved_session_id = session_id or str(uuid4())

        await self._create_session(
            session_service=session_service,
            user_id=resolved_user_id,
            session_id=resolved_session_id,
            state=context or {},
        )

        content = self._new_user_content(prompt)
        final_answer = ""
        async for event in self._run_agent(
            runner=runner,
            user_id=resolved_user_id,
            session_id=resolved_session_id,
            content=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_answer = "".join(
                    part.text or "" for part in event.content.parts if part.text
                ).strip()

        if not final_answer:
            raise RuntimeError("ADK runner completed without a final text response.")

        return final_answer

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Synchronous wrapper for scripts and tests outside an event loop."""

        return asyncio.run(self.generate_async(prompt, **kwargs))

    def _get_runner(self) -> Any:
        """Create and cache the ADK runner used for backend chat requests."""

        if self._runner is not None:
            return self._runner

        self._session_service = InMemorySessionService()
        root_agent = create_root_agent(model=self.model_name)
        self._runner = Runner(
            agent=root_agent,
            app_name=self.app_name,
            session_service=self._session_service,
        )
        return self._runner

    async def _create_session(
        self,
        *,
        session_service: Any,
        user_id: str,
        session_id: str,
        state: dict[str, Any],
    ) -> None:
        """Create an ADK session, supporting sync and async session services."""

        created = session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
            state=state,
        )
        if inspect.isawaitable(created):
            await created

    def _new_user_content(self, prompt: str) -> Any:
        """Build a GenAI user content object from a raw prompt."""

        return types.Content(role="user", parts=[types.Part(text=prompt)])

    def _run_agent(
        self,
        *,
        runner: Any,
        user_id: str,
        session_id: str,
        content: Any,
    ) -> AsyncIterator[Any]:
        """Run the ADK agent and stream invocation events."""

        return runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        )
