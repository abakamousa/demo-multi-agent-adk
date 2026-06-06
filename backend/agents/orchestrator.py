"""Root orchestrator agent definition built with Google ADK."""

from google.adk.agents import Agent

from backend.agents.financial_advisor import create_financial_advisor_agent
from backend.agents.rag_subagent import create_rag_agent
from utils.config import load_settings

DEFAULT_MODEL = load_settings().adk.model_name


def create_root_agent(model: str = DEFAULT_MODEL) -> Agent:
    """Create the root ADK agent that delegates work to subagents."""

    rag_agent = create_rag_agent(model=model)
    financial_advisor_agent = create_financial_advisor_agent(model=model)

    return Agent(
        name="multi_agent_orchestrator",
        model=model,
        description=(
            "Routes user requests to specialist agents for research and financial "
            "education tasks."
        ),
        instruction=(
            "You are the coordinator for a small multi-agent backend. Delegate "
            "financial, investing, market, budgeting, and portfolio questions to "
            "financial_advisor_agent. Delegate factual, retrieval, or general "
            "research questions to rag_research_agent. Return a concise final answer "
            "to the user."
        ),
        sub_agents=[rag_agent, financial_advisor_agent],
    )
