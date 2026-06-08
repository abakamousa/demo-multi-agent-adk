"""Financial advisor subagent definition built with Google ADK."""

from google.adk.agents import Agent
from google.genai import types

from utils.config import load_settings

settings = load_settings()
DEFAULT_MODEL = settings.adk.model_name


def calculate_compound_growth(
    principal: float,
    annual_rate_percent: float,
    years: float,
    monthly_contribution: float = 0.0,
) -> dict[str, float]:
    """Project future value with monthly contributions and compound growth.

    Args:
        principal: Starting amount.
        annual_rate_percent: Expected annual return percentage, for example 7 for 7%.
        years: Projection length in years.
        monthly_contribution: Optional amount added at the end of each month.

    Returns:
        Future value, total contributions, and growth amount.
    """

    if principal < 0:
        raise ValueError("principal must be non-negative")
    if years < 0:
        raise ValueError("years must be non-negative")
    if monthly_contribution < 0:
        raise ValueError("monthly_contribution must be non-negative")

    months = round(years * 12)
    monthly_rate = annual_rate_percent / 100 / 12
    future_value = principal

    for _ in range(months):
        future_value = future_value * (1 + monthly_rate) + monthly_contribution

    total_contributions = principal + (monthly_contribution * months)
    growth = future_value - total_contributions

    return {
        "future_value": round(future_value, 2),
        "total_contributions": round(total_contributions, 2),
        "growth": round(growth, 2),
    }


def calculate_loan_payment(
    principal: float,
    annual_rate_percent: float,
    years: float,
) -> dict[str, float]:
    """Calculate a fixed monthly loan payment.

    Args:
        principal: Loan principal.
        annual_rate_percent: Annual interest rate percentage, for example 5.5.
        years: Loan term in years.

    Returns:
        Monthly payment, total payment, and total interest.
    """

    if principal <= 0:
        raise ValueError("principal must be positive")
    if years <= 0:
        raise ValueError("years must be positive")

    months = round(years * 12)
    monthly_rate = annual_rate_percent / 100 / 12

    if monthly_rate == 0:
        monthly_payment = principal / months
    else:
        monthly_payment = (
            principal
            * monthly_rate
            * (1 + monthly_rate) ** months
            / ((1 + monthly_rate) ** months - 1)
        )

    total_payment = monthly_payment * months
    total_interest = total_payment - principal

    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
    }


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
            "materially change the answer. Use the available calculator tools for "
            "compound-growth, savings, loan, and debt-payment math instead of doing "
            "the arithmetic manually. State key assumptions such as rate, term, and "
            "contribution amount."
        ),
        tools=[
            calculate_compound_growth,
            calculate_loan_payment,
        ],
        generate_content_config=types.GenerateContentConfig(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    initial_delay=settings.adk.retry_initial_delay,
                    attempts=settings.adk.retry_attempts,
                )
            )
        ),
    )
