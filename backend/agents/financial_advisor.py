"""Financial advisor subagent definition built with Google ADK."""

from google.adk.agents import Agent
from google.genai import types

from utils.config import load_settings

settings = load_settings()
DEFAULT_MODEL = settings.adk.model_name


def create_financial_advisor_agent(model: str = DEFAULT_MODEL) -> Agent:
    """Create the specialist ADK agent for financial education tasks."""

    return Agent(
        name="financial_advisor_agent",
        model=model,
        description=(
            "Handles financial, investing, market, budgeting, and portfolio-analysis "
            "questions with educational guidance."
        ),
        instruction=(
            "You are a careful financial education agent. Provide general information "
            "and explain tradeoffs clearly. Do not present guidance as personalized "
            "investment, tax, or legal advice. Ask for missing assumptions when they "
            "materially change the answer."
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
