"""Pydantic models used by the backend."""

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request payload accepted by the backend chat endpoint."""

    prompt: str = Field(..., description="The user query for the multi-agent backend")
    user_id: str | None = Field(None, description="Optional user identifier")
    context: dict[str, Any] | None = Field(
        None, description="Optional context metadata"
    )


class QueryResponse(BaseModel):
    """Response payload returned by the backend chat endpoint."""

    answer: str = Field(..., description="Generated answer from the LLM")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Response metadata and trace info"
    )
