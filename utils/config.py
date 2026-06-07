"""Validated application configuration loaded from YAML."""

from functools import lru_cache
from os import getenv
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr, ValidationError

CONFIG_FILE = "config.yaml"
EXAMPLE_CONFIG_FILE = "config.example.yaml"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / CONFIG_FILE
EXAMPLE_CONFIG_PATH = PROJECT_ROOT / EXAMPLE_CONFIG_FILE
ENVIRONMENT_VARIABLE = "APP_ENV"


class AppConfig(BaseModel):
    """Configuration used by the Streamlit frontend."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    page_icon: str = Field(min_length=1)
    layout: Literal["centered", "wide"]
    backend_url: HttpUrl
    prompt_label: str = Field(min_length=1)


class BackendConfig(BaseModel):
    """Configuration used by the FastAPI backend."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    version: str = Field(min_length=1)


class ADKConfig(BaseModel):
    """Configuration for Google ADK agent execution."""

    model_config = ConfigDict(extra="forbid")

    app_name: str = Field(min_length=1)
    default_user_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    retry_attempts: int = Field(default=2, ge=1)
    retry_initial_delay: float = Field(default=1.0, gt=0)


class VertexAIConfig(BaseModel):
    """Configuration for Google Cloud Vertex AI defaults."""

    model_config = ConfigDict(extra="forbid")

    auth_method: Literal["gemini_api_key", "vertex_ai"] = "gemini_api_key"
    project: str | None = None
    region: str = Field(min_length=1)
    google_api_key: SecretStr | None = None


class LangfuseConfig(BaseModel):
    """Configuration for Langfuse tracing."""

    model_config = ConfigDict(extra="forbid")

    public_key: SecretStr | None = None
    secret_key: SecretStr | None = None
    base_url: HttpUrl
    backend_trace_name: str = Field(min_length=1)
    frontend_trace_name: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class Settings(BaseModel):
    """Top-level validated settings for the application."""

    model_config = ConfigDict(extra="forbid")

    app: AppConfig
    backend: BackendConfig
    adk: ADKConfig
    vertex_ai: VertexAIConfig
    langfuse: LangfuseConfig


class EnvironmentSettingsFile(BaseModel):
    """Validated multi-environment configuration file."""

    model_config = ConfigDict(extra="forbid")

    default_environment: str = Field(min_length=1)
    environments: dict[str, Settings] = Field(min_length=1)

    def select(self, environment: str | None = None) -> Settings:
        """Return settings for the requested environment."""

        selected_environment = environment or getenv(
            ENVIRONMENT_VARIABLE, self.default_environment
        )
        try:
            return self.environments[selected_environment]
        except KeyError as exc:
            available = ", ".join(sorted(self.environments))
            raise ValueError(
                f"Unknown config environment '{selected_environment}'. "
                f"Available environments: {available}."
            ) from exc


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML config file and return a mapping."""

    with path.open("r", encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file)

    if not isinstance(raw_config, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {path}")

    return raw_config


def _default_config_path() -> Path:
    """Use local config when present, otherwise use the committed example."""

    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH
    return EXAMPLE_CONFIG_PATH


@lru_cache(maxsize=1)
def load_settings(
    config_path: str | Path | None = None,
    environment: str | None = None,
) -> Settings:
    """Load and validate application settings from YAML."""

    load_dotenv()
    path = Path(config_path) if config_path is not None else _default_config_path()
    try:
        raw_config = _read_yaml(path)
        if "environments" in raw_config:
            return EnvironmentSettingsFile.model_validate(raw_config).select(
                environment=environment
            )
        return Settings.model_validate(raw_config)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration in {path}: {exc}") from exc
