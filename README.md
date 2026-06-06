# demo-multi-agent-adk

Python demo for a multi-agent application built with Google ADK, FastAPI, Streamlit, Vertex AI/Gemini, and LangSmith tracing.

## Overview

`demo-multi-agent-adk` separates a Streamlit frontend from a FastAPI backend. The backend exposes a chat endpoint, runs a Google ADK root agent through an ADK `Runner`, and delegates work to specialist subagents for retrieval-style answers and financial education. Shared runtime settings live in `config.yaml` and are validated with Pydantic before use.

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/bf9c6b0c-fcc4-4495-add8-e1258a3d2abd" />


## Project Structure

```text
app/
  main.py
  service/
    vertex_llm.py
  utils/
    monitoring.py
    pydantic.py

backend/
  main.py
  api/
    routes.py
  agents/
    orchestrator.py
    rag_subagent.py
    financial_advisor.py
  service/
    vertex_llm.py
  utils/
    monitoring.py
    pydantic.py

utils/
  config.py

tests/
  test_app.py
  test_backend.py
  test_config.py
  test_service.py

config.yaml
pyproject.toml
```

## Requirements

- Python 3.11+
- `uv`
- Google ADK and LangSmith dependencies from `pyproject.toml`
- Google Cloud credentials for live Vertex AI/Gemini calls

## Setup

Install dependencies with `uv`:

```bash
uv sync
```

Install development dependencies:

```bash
uv sync --extra dev
```

## Configuration

Application configuration is centralized in [config.yaml](config.yaml):

```yaml
app:
  title: "Multi-Agent ADK Demo"
  backend_url: "http://localhost:8000"

adk:
  app_name: "demo_multi_agent_adk"
  default_user_id: "anonymous"
  model_name: "gemini-flash-latest"

vertex_ai:
  project: null
  region: "us-central1"
```

The config is loaded and validated by [utils/config.py](utils/config.py). Unknown keys, invalid frontend layouts, malformed URLs, and missing required values fail validation early.

Update `config.yaml` for local environment values such as:

- `app.backend_url`
- `adk.model_name`
- `vertex_ai.project`
- `vertex_ai.region`
- LangSmith trace names and tags

## LangSmith Tracing

The app uses the official LangSmith Google ADK integration via `configure_google_adk()`. Configure tracing with environment variables:

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="your-langsmith-api-key"
export LANGSMITH_PROJECT="demo-multi-agent-adk"
```

Tracing is configured in:

- [backend/utils/monitoring.py](backend/utils/monitoring.py)
- [app/utils/monitoring.py](app/utils/monitoring.py)

ADK agent runs, LLM calls, and tool calls are traced automatically after configuration.

## Running The Backend

Start the FastAPI backend:

```bash
uv run uvicorn backend.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/healthz
```

Chat endpoint:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What should I know about market risk?", "user_id": "local-user"}'
```

## Running The Frontend

Start the Streamlit app:

```bash
uv run streamlit run app/main.py
```

The frontend reads display settings and backend URL from `config.yaml`.

## Agents

The backend agents are defined in `backend/agents/`:

- `orchestrator.py`: root ADK agent that delegates to specialist subagents.
- `rag_subagent.py`: retrieval-focused research agent.
- `financial_advisor.py`: financial education agent.

The service in [backend/service/vertex_llm.py](backend/service/vertex_llm.py) creates an ADK `Runner`, an `InMemorySessionService`, a user message, and returns the final text response from the ADK event stream.

## Testing

Run the test suite:

```bash
uv run --extra dev pytest
```

Run formatting:

```bash
uv run --extra dev black app backend tests utils
```

Run linting:

```bash
uv run --extra dev ruff check .
```

## Notes

- `config.yaml` is the source of truth for runtime configuration.
- Keep secrets out of `config.yaml`; use environment variables or deployment secret management.
- The frontend service is still a lightweight local client layer. The backend is the ADK execution path.
- See [images/architecture.png](images/architecture.png) for the architecture diagram.
