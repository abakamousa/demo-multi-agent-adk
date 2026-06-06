"""Unit tests for the backend package."""

from backend.api.routes import router


def test_backend_router_exists() -> None:
    assert router is not None
    assert len(router.routes) >= 1
