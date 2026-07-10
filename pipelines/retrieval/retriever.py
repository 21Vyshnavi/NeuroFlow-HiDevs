import asyncio
import json
import logging
from typing import List, Dict, Any
from backend.db.pool import db_pool
from backend.providers.client import client as llm_client
from pipelines.retrieval import RetrievalResult
from pipelines.retrieval.query_processor import process_query
from pipelines.retrieval.fusion import reciprocal_rank_fusion
from pipelines.retrieval.reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)

from opentelemetry import trace
import time

tracer = trace.get_tracer("neuroflow.retrieval")

class HybridRetriever:
    def __init__(self, use_local_reranker: bool = False):
        self.reranker = CrossEncoderReranker(use_local=use_local_reranker)

    async def _dense_retrieval(self, query: str, k: int, expanded_queries: List[str]) -> List[RetrievalResult]:
        with tracer.start_as_current_span("retrieval.dense"):
            pool = db_pool.get_pool()
            if not pool:
                return []

            # Gather embeddings for original + expanded queries
            queries_to_embed = [query] + expanded_queries
            try:
                embeddings = await llm_client.embed(queries_to_embed)
            except Exception as e:
                logger.error(f"Dense retrieval embedding failed: {e}")
                return []

            results = []
            async with pool.acquire() as conn:
                for emb in embeddings:
                    rows = await conn.fetch(
                        """
                        SELECT c.id, c.document_id, c.content, c.metadata, d.filename, (1 - (c.embedding <=> $1)) as score
                        FROM chunks c
                        JOIN documents d ON c.document_id = d.id
                        ORDER BY c.embedding <=> $1
                        LIMIT $2
                        """,
                        emb,
                        k
                    )
                    for r in rows:
                        meta = json.loads(r["metadata"])
                        meta["filename"] = r["filename"]
                        results.append(RetrievalResult(
                            chunk_id=str(r["id"]),
                            document_id=str(r["document_id"]),
                            content=r["content"],
                            score=float(r["score"]),
                            metadata=meta
                        ))
            return results

    async def _sparse_retrieval(self, query: str, k: int) -> List[RetrievalResult]:
        with tracer.start_as_current_span("retrieval.sparse"):
            pool = db_pool.get_pool()
            if not pool:
                return []

            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT c.id, c.document_id, c.content, c.metadata, d.filename, ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', $1)) as score
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', $1)
                    ORDER BY score DESC
                    LIMIT $2
                    """,
                    query,
                    k
                )
                return [
                    RetrievalResult(
                        chunk_id=str(r["id"]),
                        document_id=str(r["document_id"]),
                        content=r["content"],
                        score=float(r["score"]),
                        metadata={**json.loads(r["metadata"]), "filename": r["filename"]}
                    ) for r in rows
                ]

    async def _metadata_retrieval(self, query: str, filters: Dict[str, Any], k: int) -> List[RetrievalResult]:
        with tracer.start_as_current_span("retrieval.metadata"):
            pool = db_pool.get_pool()
            if not pool or not filters:
                return []

            # Check if we have an embedding to sort by
            try:
                emb = (await llm_client.embed([query]))[0]
            except Exception:
                return []

            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT c.id, c.document_id, c.content, c.metadata, d.filename, (1 - (c.embedding <=> $2)) as score
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE c.metadata @> $1::jsonb
                    ORDER BY c.embedding <=> $2
                    LIMIT $3
                    """,
                    json.dumps(filters),
                    emb,
                    k
                )
                return [
                    RetrievalResult(
                        chunk_id=str(r["id"]),
                        document_id=str(r["document_id"]),
                        content=r["content"],
                        score=float(r["score"]),
                        metadata={**json.loads(r["metadata"]), "filename": r["filename"]}
                    ) for r in rows
                ]

    async def retrieve(self, query: str, k: int = 20) -> List[RetrievalResult]:
        start_time = time.time()
        with tracer.start_as_current_span("retrieval.pipeline") as span:
            span.set_attribute("query", query)
            
            # Step 1: Process query (expansion, metadata detection)
            processed = await process_query(query)
            
            # Step 2: Run retrievers in parallel
            dense_task = self._dense_retrieval(query, k, processed.expanded_queries)
            sparse_task = self._sparse_retrieval(query, k)
            meta_task = self._metadata_retrieval(query, processed.metadata_filters, k)

            dense_res, sparse_res, meta_res = await asyncio.gather(dense_task, sparse_task, meta_task)

            # Step 3: Reciprocal Rank Fusion
            with tracer.start_as_current_span("retrieval.fusion"):
                fused = reciprocal_rank_fusion([dense_res, sparse_res, meta_res])

            # Step 4: Rerank the top 40 results
            with tracer.start_as_current_span("retrieval.rerank"):
                top_candidates = fused[:40]
                reranked = await self.reranker.rerank(query, top_candidates)

            results = reranked[:k]
            span.set_attribute("retrieved_count", len(results))

            try:
                from backend.monitoring.metrics import retrieval_latency
                retrieval_latency.labels(strategy="hybrid").observe(time.time() - start_time)
            except ImportError:
                pass

            return results

