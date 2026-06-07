"""RAG subagent definition built with Google ADK."""

from google.adk.agents import Agent
from google.genai import types

from utils.config import load_settings

settings = load_settings()
DEFAULT_MODEL = settings.adk.model_name


def create_rag_agent(model: str = DEFAULT_MODEL) -> Agent:
    """Create the specialist ADK agent for retrieval-style responses."""

    return Agent(
        name="rag_research_agent",
        model=model,
        description=(
            "Answers knowledge and retrieval-style questions by synthesizing "
            "provided context and asking for clarification when context is missing."
        ),
        instruction=(
            "You are a retrieval-focused research agent. Answer from the user's "
            "prompt and any provided context. Be precise about what is known, and "
            "state when the available context is insufficient."
        ),
        generate_content_config=types.GenerateContentConfig(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    initial_delay=settings.adk.retry_initial_delay,
                    attempts=settings.adk.retry_attempts,
                )
            )
        ),
    )
