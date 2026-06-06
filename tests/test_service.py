"""Unit tests for service modules."""

from collections.abc import AsyncIterator
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from backend.service.vertex_llm import VertexLLMService


class FakeEvent:
    content = SimpleNamespace(
        parts=[
            SimpleNamespace(text="ADK generated answer"),
        ]
    )

    def is_final_response(self) -> bool:
        return True


class FakeRunner:
    async def run_async(
        self,
        *,
        user_id: str,
        session_id: str,
        new_message: object,
    ) -> AsyncIterator[FakeEvent]:
        yield FakeEvent()


class FakeSessionService:
    def create_session(self, **kwargs: object) -> object:
        return SimpleNamespace(**kwargs)


class FakeMonitor:
    @contextmanager
    def trace_agent_run(self, **kwargs: object) -> object:
        yield SimpleNamespace(update=lambda **update_kwargs: None)


class FakeVertexLLMService(VertexLLMService):
    def __init__(self) -> None:
        super().__init__()
        self.monitor = FakeMonitor()

    def _get_runner(self) -> FakeRunner:
        self._session_service = FakeSessionService()
        return FakeRunner()

    def _new_user_content(self, prompt: str) -> object:
        return {"prompt": prompt}


@pytest.mark.asyncio
async def test_backend_vertex_llm_runs_adk_agent() -> None:
    service = FakeVertexLLMService()
    output = await service.generate_async(prompt="Hello")
    assert output == "ADK generated answer"


def test_backend_vertex_llm_sync_wrapper() -> None:
    service = VertexLLMService()
    assert service.model_name == "gemini-flash-latest"
