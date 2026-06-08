"""Unit tests for service modules."""

from collections.abc import AsyncIterator
from contextlib import contextmanager
import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.service.vertex_llm import QuotaExceededError, VertexLLMService
from utils.config import load_settings


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

    def flush(self) -> None:
        return None


class FakeVertexLLMService(VertexLLMService):
    def __init__(self) -> None:
        super().__init__()
        self.monitor = FakeMonitor()

    def _get_runner(self) -> FakeRunner:
        self._session_service = FakeSessionService()
        return FakeRunner()

    def _new_user_content(self, prompt: str) -> object:
        return {"prompt": prompt}


def test_backend_exposes_health_endpoints() -> None:
    client = TestClient(app)

    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/api/health").json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_backend_vertex_llm_runs_adk_agent() -> None:
    service = FakeVertexLLMService()
    output = await service.generate_async(prompt="Hello")
    assert output == "ADK generated answer"


@pytest.mark.asyncio
async def test_backend_vertex_llm_returns_agent_trace() -> None:
    service = FakeVertexLLMService()
    result = await service.generate_with_trace_async(prompt="Hello")

    assert result["answer"] == "ADK generated answer"
    assert result["final_agent"] == "demo_multi_agent_adk"
    assert result["agent_trace"] == []


def test_backend_vertex_llm_sync_wrapper() -> None:
    service = VertexLLMService()
    assert service.model_name == load_settings().adk.model_name


def test_backend_vertex_llm_sets_google_api_key_env(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    service = VertexLLMService()
    service.google_api_key = "test-api-key"  # pragma: allowlist secret

    service._configure_google_auth()

    assert os.environ["GOOGLE_API_KEY"] == "test-api-key"  # pragma: allowlist secret
    assert os.environ["GEMINI_API_KEY"] == "test-api-key"  # pragma: allowlist secret


def test_backend_vertex_llm_reads_google_api_key_from_env(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "env-api-key")
    monkeypatch.setenv("GEMINI_API_KEY", "env-api-key")
    monkeypatch.setattr(
        "backend.service.vertex_llm.load_settings",
        lambda: SimpleNamespace(
            adk=SimpleNamespace(
                app_name="demo_multi_agent_adk",
                default_user_id="anonymous",
                model_name="gemini-2.5-flash",
            ),
            vertex_ai=SimpleNamespace(
                auth_method="gemini_api_key",
                project=None,
                region="us-central1",
                google_api_key=None,
            ),
        ),
    )

    service = VertexLLMService()

    assert service.google_api_key == "env-api-key"  # pragma: allowlist secret


def test_backend_vertex_llm_sets_vertex_ai_env(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "stale-api-key")
    monkeypatch.setenv("GEMINI_API_KEY", "stale-api-key")

    service = VertexLLMService(project="demo-project", region="us-central1")
    service.auth_method = "vertex_ai"
    service.google_api_key = "fallback-api-key"  # pragma: allowlist secret

    service._configure_google_auth()

    assert os.environ["GOOGLE_GENAI_USE_VERTEXAI"] == "true"
    assert os.environ["GOOGLE_CLOUD_PROJECT"] == "demo-project"
    assert os.environ["GOOGLE_CLOUD_LOCATION"] == "us-central1"
    assert "GOOGLE_API_KEY" not in os.environ
    assert "GEMINI_API_KEY" not in os.environ


def test_backend_vertex_llm_uses_gemini_api_key_mode_by_default(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)

    service = VertexLLMService()
    service.auth_method = "gemini_api_key"
    service.google_api_key = "test-api-key"  # pragma: allowlist secret

    service._configure_google_auth()

    assert os.environ["GOOGLE_API_KEY"] == "test-api-key"  # pragma: allowlist secret
    assert os.environ["GEMINI_API_KEY"] == "test-api-key"  # pragma: allowlist secret
    assert "GOOGLE_GENAI_USE_VERTEXAI" not in os.environ


def test_backend_vertex_llm_extracts_retry_delay() -> None:
    service = VertexLLMService()
    message = "Please retry in 28.120023597s. RESOURCE_EXHAUSTED"

    assert service._is_quota_error(ValueError(message))
    assert service._extract_retry_after_seconds(message) == 28.120023597
