"""Validated application configuration loaded from ``config.yaml``."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError

CONFIG_FILE = "config.yaml"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / CONFIG_FILE


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


class VertexAIConfig(BaseModel):
    """Configuration for Google Cloud Vertex AI defaults."""

    model_config = ConfigDict(extra="forbid")

    project: str | None = None
    region: str = Field(min_length=1)


class LangSmithConfig(BaseModel):
    """Configuration for LangSmith Google ADK tracing."""

    model_config = ConfigDict(extra="forbid")

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
    langsmith: LangSmithConfig


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML config file and return a mapping."""

    with path.open("r", encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file)

    if not isinstance(raw_config, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {path}")

    return raw_config


@lru_cache(maxsize=1)
def load_settings(config_path: str | Path = DEFAULT_CONFIG_PATH) -> Settings:
    """Load and validate application settings from YAML."""

    path = Path(config_path)
    try:
        return Settings.model_validate(_read_yaml(path))
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration in {path}: {exc}") from exc
