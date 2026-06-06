"""Unit tests for shared YAML configuration validation."""

import pytest

from utils.config import Settings, load_settings


def test_load_settings_from_default_yaml() -> None:
    """Validate the repository config file."""

    settings = load_settings()

    assert settings.adk.model_name
    assert settings.vertex_ai.region
    assert settings.app.backend_url.scheme in {"http", "https"}


def test_load_settings_rejects_unknown_keys(tmp_path) -> None:
    """Reject unexpected config keys so typos do not pass silently."""

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
app:
  title: Demo
  page_icon: ":robot_face:"
  layout: centered
  backend_url: "http://localhost:8000"
  prompt_label: Prompt
  typo: unexpected
backend:
  title: Backend
  description: Backend description
  version: "0.1.0"
adk:
  app_name: demo
  default_user_id: anonymous
  model_name: gemini-flash-latest
vertex_ai:
  project: null
  region: us-central1
langsmith:
  backend_trace_name: demo.backend
  frontend_trace_name: demo.frontend
  tags:
    - google-adk
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid configuration"):
        load_settings(config_file)


def test_settings_rejects_invalid_layout() -> None:
    """Validate constrained frontend layout values."""

    config = load_settings().model_dump(mode="json")
    config["app"]["layout"] = "full"

    with pytest.raises(ValueError):
        Settings.model_validate(config)
