"""Pydantic models used by the frontend."""

from pydantic import BaseModel, Field


class UserQuery(BaseModel):
    query: str = Field(..., description="User prompt for the multi-agent system")
    user_id: str | None = Field(None, description="Optional user identifier")
