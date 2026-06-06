"""FastAPI route definitions for the backend API."""

from fastapi import APIRouter, HTTPException
from backend.service.vertex_llm import VertexLLMService
from backend.utils.pydantic import QueryRequest, QueryResponse
from backend.utils.monitoring import LangfuseMonitor

router = APIRouter()
service = VertexLLMService()
monitor = LangfuseMonitor()


@router.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest) -> QueryResponse:
    """Handle a chat request by invoking the ADK-backed LLM service."""

    monitor.track_event("backend.request", payload=request.model_dump())

    try:
        answer = await service.generate_async(
            prompt=request.prompt,
            user_id=request.user_id,
            context=request.context,
        )
        monitor.track_event("backend.response", payload={"answer": answer})
        return QueryResponse(answer=answer, metadata={"source": "google-adk"})
    except Exception as exc:
        monitor.track_event("backend.error", payload={"error": str(exc)})
        raise HTTPException(
            status_code=500, detail="Failed to generate the LLM response."
        )
