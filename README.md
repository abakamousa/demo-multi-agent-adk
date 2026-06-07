# Demo-multi-agent-adk

Python demo for a multi-agent application built with Google ADK, FastAPI, Streamlit, Vertex AI/Gemini, and Langfuse tracing.

## Overview

`demo-multi-agent-adk` separates a Streamlit frontend from a FastAPI backend. The backend exposes a chat endpoint, runs a Google ADK root agent through an ADK `Runner`, and delegates work to specialist subagents for retrieval-style answers and financial education. Shared runtime settings live in a local `config.yaml` and are validated with Pydantic before use. Commit only `config.example.yaml`; keep real credentials in the ignored local config file or environment variables.

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

config.example.yaml
pyproject.toml
```

## Requirements

- Python 3.11+
- `uv`
- Google ADK and Langfuse dependencies from `pyproject.toml`
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

Application configuration is defined by environment in [config.example.yaml](config.example.yaml). Copy it locally before running the app:

```bash
cp config.example.yaml config.yaml
```

`config.yaml` is ignored by Git so it can contain local URLs and credentials without being pushed.

```yaml
default_environment: "dev"

environments:
  dev:
    app:
      backend_url: "http://localhost:8000"
    vertex_ai:
      project: null
      region: "us-central1"
      google_api_key: null
    langfuse:
      public_key: null
      secret_key: null
      base_url: "https://cloud.langfuse.com"
```

The config is loaded and validated by [utils/config.py](utils/config.py). Unknown keys, invalid frontend layouts, malformed URLs, unknown environments, and missing required values fail validation early.

Choose the active environment with `APP_ENV`:

```bash
export APP_ENV=dev
```

For production:

```bash
export APP_ENV=prod
```

Update the ignored local `config.yaml` for environment-specific values such as:

- `app.backend_url`
- `adk.model_name`
- `vertex_ai.project`
- `vertex_ai.region`
- `vertex_ai.google_api_key`
- Langfuse trace names and tags
- `langfuse.public_key`
- `langfuse.secret_key`
- `langfuse.base_url`

When `vertex_ai.google_api_key` is set, the backend exports it to `GOOGLE_API_KEY`
before creating the ADK runner. You can still leave it `null` and provide
`GOOGLE_API_KEY` from the shell instead.

## Langfuse Tracing

The backend traces Google ADK runs with the Langfuse Python SDK. Each `/api/chat` request creates an `agent` observation around the ADK runner, propagates `user_id`, `session_id`, tags, and metadata, and records the prompt plus final answer.

Configure Langfuse with environment variables or the ignored local `config.yaml`.

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"
```

For US cloud, use:

```bash
export LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"
```

Tracing helpers live in:

- [backend/utils/monitoring.py](backend/utils/monitoring.py)
- [app/utils/monitoring.py](app/utils/monitoring.py)

Trace names, tags, and optional Langfuse keys are configured per environment:

```yaml
environments:
  dev:
    langfuse:
      public_key: null
      secret_key: null
      base_url: "https://cloud.langfuse.com"
      backend_trace_name: "demo_multi_agent_adk.backend.dev"
      frontend_trace_name: "demo_multi_agent_adk.frontend.dev"
      tags:
        - "google-adk"
        - "dev"
```

The backend service instrumentation is in [backend/service/vertex_llm.py](backend/service/vertex_llm.py). It follows Langfuse best practices for agent workflows by using a descriptive trace name, explicit input/output, propagated session/user attributes, and error status updates.

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

The frontend reads display settings and backend URL from the selected config environment.

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

- `config.example.yaml` is the committed template.
- `config.yaml` is ignored and may contain local credentials.
- Prefer environment variables or deployment secret management for production secrets.
- The frontend service is still a lightweight local client layer. The backend is the ADK execution path.
- See [images/architecture.png](images/architecture.png) for the architecture diagram.
