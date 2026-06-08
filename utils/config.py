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
    cors_allowed_origins: list[str] = Field(default_factory=list)


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


def _env_value(name: str) -> str | None:
    """Return a non-empty environment variable value."""

    value = getenv(name)
    if value is None or value == "":
        return None
    return value


def _env_list(name: str) -> list[str] | None:
    """Return a comma-separated environment variable as a list."""

    value = _env_value(name)
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _apply_env_overrides(settings: Settings) -> Settings:
    """Apply deployment-friendly environment variable overrides."""

    raw_settings = settings.model_dump(mode="python")

    scalar_overrides = {
        ("app", "backend_url"): _env_value("APP_BACKEND_URL"),
        ("app", "title"): _env_value("APP_TITLE"),
        ("app", "prompt_label"): _env_value("APP_PROMPT_LABEL"),
        ("adk", "model_name"): _env_value("ADK_MODEL_NAME"),
        ("vertex_ai", "auth_method"): _env_value("VERTEX_AI_AUTH_METHOD"),
        ("vertex_ai", "project"): _env_value("VERTEX_AI_PROJECT"),
        ("vertex_ai", "region"): _env_value("VERTEX_AI_REGION"),
        ("vertex_ai", "google_api_key"): _env_value("GOOGLE_API_KEY")
        or _env_value("GEMINI_API_KEY"),
        ("langfuse", "public_key"): _env_value("LANGFUSE_PUBLIC_KEY"),
        ("langfuse", "secret_key"): _env_value("LANGFUSE_SECRET_KEY"),
        ("langfuse", "base_url"): _env_value("LANGFUSE_BASE_URL"),
        ("langfuse", "backend_trace_name"): _env_value("LANGFUSE_BACKEND_TRACE_NAME"),
        ("langfuse", "frontend_trace_name"): _env_value("LANGFUSE_FRONTEND_TRACE_NAME"),
    }

    for path, value in scalar_overrides.items():
        if value is None:
            continue
        section, key = path
        raw_settings[section][key] = value

    cors_allowed_origins = _env_list("BACKEND_CORS_ALLOWED_ORIGINS")
    if cors_allowed_origins is not None:
        raw_settings["backend"]["cors_allowed_origins"] = cors_allowed_origins

    langfuse_tags = _env_list("LANGFUSE_TAGS")
    if langfuse_tags is not None:
        raw_settings["langfuse"]["tags"] = langfuse_tags

    return Settings.model_validate(raw_settings)


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
            settings = EnvironmentSettingsFile.model_validate(raw_config).select(
                environment=environment
            )
        else:
            settings = Settings.model_validate(raw_config)
        return _apply_env_overrides(settings)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration in {path}: {exc}") from exc
