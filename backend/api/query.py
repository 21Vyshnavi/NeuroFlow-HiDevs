# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import json
import uuid

from fastapi import APIRouter
from fastapi import Query as FastAPIQuery
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from pipelines.generation.generator import run_generation_pipeline

router = APIRouter(prefix="/query", tags=["query"])

class QueryRequest(BaseModel):
    query: str
    pipeline_id: str | None = None
    stream: bool = False

from fastapi import APIRouter, Depends

from backend.security.auth import ScopeRequired
from backend.security.prompt_injection import classify_prompt_injection
from backend.security.validators import validate_query_text


@router.post("")
async def execute_query(
    payload: QueryRequest,
    _user = Depends(ScopeRequired("query"))
):
    # Validate and sanitize input
    sanitized_query = validate_query_text(payload.query)
    payload.query = sanitized_query

    # Prompt injection classification (both pattern and LLM classification)
    await classify_prompt_injection(payload.query)

    run_id = str(uuid.uuid4())
    # Return immediately if streaming requested, else execute synchronously
    if payload.stream:
        return {"run_id": run_id, "status": "streaming_ready"}
    else:
        # Simple non-stream wrapper mock
        accumulator = []
        async for event in run_generation_pipeline(run_id, payload.query, payload.pipeline_id):
            if event["type"] == "token":
                accumulator.append(event["delta"])
        return {
            "run_id": run_id,
            "response": "".join(accumulator),
            "status": "complete"
        }

@router.get("/{run_id}/stream")
async def get_stream(
    run_id: str,
    pipeline_id: str | None = None,
    q: str = FastAPIQuery(...),
    _user = Depends(ScopeRequired("query"))
):
    # Validate and sanitize input
    q = validate_query_text(q)
    
    async def event_generator():
        # Yield keepalive and stream updates
        try:
            async for update in run_generation_pipeline(run_id, q, pipeline_id):
                yield {"data": json.dumps(update)}
        except Exception as e:
            yield {"data": json.dumps({"type": "error", "message": str(e)})}
            
    return EventSourceResponse(event_generator())
