"""FastAPI route definitions for the backend API."""

import logging

from fastapi import APIRouter, HTTPException, status
from backend.service.vertex_llm import QuotaExceededError, VertexLLMService
from backend.utils.pydantic import QueryRequest, QueryResponse
from backend.utils.monitoring import LangfuseMonitor

logger = logging.getLogger(__name__)

router = APIRouter()
service = VertexLLMService()
monitor = LangfuseMonitor()


@router.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest) -> QueryResponse:
    """Handle a chat request by invoking the ADK-backed LLM service."""

    logger.info(
        "Received /api/chat request user_id=%s has_context=%s prompt=%r",
        request.user_id or "anonymous",
        bool(request.context),
        request.prompt[:120],
    )
    monitor.track_event("backend.request", payload=request.model_dump())

    try:
        result = await service.generate_with_trace_async(
            prompt=request.prompt,
            user_id=request.user_id,
            context=request.context,
        )
        answer = result["answer"]
        logger.info(
            "Completed /api/chat request agent=%s answer=%r",
            result["final_agent"],
            answer[:120],
        )
        monitor.track_event("backend.response", payload={"answer": answer})
        return QueryResponse(
            answer=answer,
            metadata={
                "source": "google-adk",
                "final_agent": result["final_agent"],
                "agent_trace": result["agent_trace"],
            },
        )
    except QuotaExceededError as exc:
        logger.warning("Quota exceeded for /api/chat: %s", exc)
        monitor.track_event("backend.error", payload={"error": str(exc)})
        headers = {}
        if exc.retry_after_seconds is not None:
            headers["Retry-After"] = str(int(exc.retry_after_seconds))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Gemini quota exceeded. Retry later or switch quota/billing.",
                "retry_after_seconds": exc.retry_after_seconds,
                "provider_error": str(exc),
            },
            headers=headers,
        )
    except Exception as exc:
        logger.exception("Failed /api/chat request: %s", exc)
        monitor.track_event("backend.error", payload={"error": str(exc)})
        raise HTTPException(
            status_code=500, detail="Failed to generate the LLM response."
        )
