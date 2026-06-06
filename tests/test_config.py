"""Unit tests for shared YAML configuration validation."""

import pytest

from utils.config import EnvironmentSettingsFile, Settings, load_settings


def test_load_settings_from_default_yaml() -> None:
    """Validate the default local or example config file."""

    settings = load_settings()

    assert settings.adk.model_name
    assert settings.vertex_ai.region
    assert settings.app.backend_url.scheme in {"http", "https"}
    assert str(settings.langfuse.base_url).startswith("https://")


def test_load_settings_rejects_unknown_keys(tmp_path) -> None:
    """Reject unexpected config keys so typos do not pass silently."""

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
default_environment: dev
environments:
  dev:
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
    langfuse:
      public_key: null
      secret_key: null
      base_url: "https://cloud.langfuse.com"
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


def test_load_settings_selects_requested_environment(tmp_path) -> None:
    """Select a named environment from the config file."""

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
default_environment: dev
environments:
  dev:
    app:
      title: Dev
      page_icon: ":robot_face:"
      layout: centered
      backend_url: "http://localhost:8000"
      prompt_label: Prompt
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
    langfuse:
      public_key: null
      secret_key: null
      base_url: "https://cloud.langfuse.com"
      backend_trace_name: demo.backend.dev
      frontend_trace_name: demo.frontend.dev
      tags:
        - dev
  prod:
    app:
      title: Prod
      page_icon: ":robot_face:"
      layout: centered
      backend_url: "https://api.example.com"
      prompt_label: Prompt
    backend:
      title: Backend
      description: Backend description
      version: "0.1.0"
    adk:
      app_name: demo
      default_user_id: anonymous
      model_name: gemini-flash-latest
    vertex_ai:
      project: production-project
      region: us-central1
    langfuse:
      public_key: pk-lf-test
      secret_key: sk-lf-test
      base_url: "https://us.cloud.langfuse.com"
      backend_trace_name: demo.backend.prod
      frontend_trace_name: demo.frontend.prod
      tags:
        - prod
""",
        encoding="utf-8",
    )

    settings = load_settings(config_file, "prod")

    assert settings.app.title == "Prod"
    assert settings.vertex_ai.project == "production-project"
    assert settings.langfuse.public_key is not None


def test_environment_config_rejects_unknown_environment() -> None:
    """Raise a helpful error when the requested environment is missing."""

    config = load_settings().model_dump(mode="json")
    environment_file = EnvironmentSettingsFile.model_validate(
        {"default_environment": "dev", "environments": {"dev": config}}
    )

    with pytest.raises(ValueError, match="Unknown config environment"):
        environment_file.select("prod")
