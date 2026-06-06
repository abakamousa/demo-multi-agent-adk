"""Unit tests for the frontend app package."""

from app.utils.pydantic import UserQuery


def test_user_query_model() -> None:
    model = UserQuery(query="What is the latest market trend?")
    assert model.query.startswith("What")
