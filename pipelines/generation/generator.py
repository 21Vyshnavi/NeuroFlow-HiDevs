from opentelemetry import trace
import time
import uuid
import json
import logging
import redis.asyncio as redis
from typing import AsyncGenerator
from backend.db.pool import db_pool
from backend.config import settings
from backend.providers.client import client as llm_client
from backend.providers.base import ChatMessage
from backend.providers.router import RoutingCriteria
from pipelines.retrieval.retriever import HybridRetriever
from pipelines.retrieval.context_assembler import assemble_context
from pipelines.retrieval.query_processor import process_query
from pipelines.generation.prompt_builder import build_prompt
from pipelines.generation.citations import parse_citations

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("neuroflow.generation")

async def run_generation_pipeline(run_id: str, query: str, pipeline_id: str) -> AsyncGenerator[dict, None]:
    pool = db_pool.get_pool()
    if not pool:
        logger.error("DB Pool not initialized")
        return

    with tracer.start_as_current_span("generation.pipeline") as pipeline_span:
        pipeline_span.set_attribute("run_id", run_id)
        pipeline_span.set_attribute("pipeline_id", pipeline_id or "default")

        # Phase 1: Retrieval Start Event
        yield {"type": "retrieval_start"}
        start_time = time.time()

        # Query expansion & type extraction
        pq = await process_query(query)

        # Parallel retrieval
        retriever = HybridRetriever()
        results = await retriever.retrieve(query, k=8)

        # Format Context Window
        context_data = assemble_context(results)
        
        yield {
            "type": "retrieval_complete",
            "chunk_count": len(results),
            "sources": [c.metadata.get("filename", "doc") for c in results]
        }

        with tracer.start_as_current_span("generation.prompt_build"):
            # Assembling prompt and logging to postgres
            full_prompt = build_prompt(pq.query_type, context_data["context"], query)
        
        with tracer.start_as_current_span("generation.log_run"):
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO pipeline_runs (id, pipeline_id, query, retrieved_chunk_ids, status)
                    VALUES ($1, $2, $3, $4, 'running')
                    """,
                    uuid.UUID(run_id),
                    uuid.UUID(pipeline_id) if pipeline_id else None,
                    query,
                    [uuid.UUID(cid) for cid in context_data["chunks_used"]]
                )

        # Stream generation
        criteria = RoutingCriteria(task_type="rag_generation")
        accumulated_content = []
        
        status = "success"
        
        with tracer.start_as_current_span("generation.llm_call"):
            try:
                messages = [
                    ChatMessage(role="system", content="You are a helpful assistant."),
                    ChatMessage(role="user", content=full_prompt)
                ]
                
                async for token in llm_client.stream(messages, criteria):
                    accumulated_content.append(token)
                    yield {"type": "token", "delta": token}
            except Exception as e:
                logger.error(f"Generation error: {e}")
                status = "error"
                yield {"type": "token", "delta": f"Error during generation: {e}"}

        final_generation = "".join(accumulated_content)
        latency = int((time.time() - start_time) * 1000)

        with tracer.start_as_current_span("generation.citation_parse"):
            # Parse Citations
            citations = parse_citations(final_generation, context_data["sources"])

        with tracer.start_as_current_span("generation.log_run"):
            # Update database metrics
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE pipeline_runs
                    SET generation = $2, latency_ms = $3, status = 'complete', model_used = $4
                    WHERE id = $1
                    """,
                    uuid.UUID(run_id),
                    final_generation,
                    latency,
                    "gpt-4o-mini"
                )

        # Asynchronously enqueue evaluation task
        try:
            r = redis.Redis(host=settings.redis_host, port=settings.redis_port, password=settings.redis_password)
            eval_payload = {"run_id": run_id, "generation": final_generation, "context": context_data["context"]}
            await r.lpush("queue:evaluation", json.dumps(eval_payload))
            await r.aclose()
        except Exception as e:
            logger.warning(f"Could not enqueue evaluation job: {e}")

        # Metrics update
        try:
            from backend.monitoring.metrics import queries_total, generation_latency
            queries_total.labels(pipeline_id=pipeline_id or "default", status=status).inc()
            generation_latency.labels(model="gpt-4o-mini").observe(latency / 1000.0)
        except ImportError:
            pass

        yield {
            "type": "done",
            "run_id": run_id,
            "citations": [
                {
                    "source": c.reference,
                    "chunk_id": str(c.chunk_id),
                    "document": c.document_name,
                    "page": c.page_number
                } for c in citations
            ]
        }

