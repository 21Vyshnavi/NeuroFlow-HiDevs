import asyncio
import logging
from typing import List
from backend.providers.client import client as llm_client
from backend.providers.base import ChatMessage
from backend.providers.router import RoutingCriteria
from pipelines.retrieval import RetrievalResult

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    def __init__(self, use_local: bool = False):
        self.use_local = use_local
        self._model = None
        if self.use_local:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            except Exception as e:
                logger.warning(f"Could not load local CrossEncoder: {e}. Falling back to API-based.")
                self.use_local = False

    async def rerank(self, query: str, candidates: List[RetrievalResult]) -> List[RetrievalResult]:
        if not candidates:
            return []

        if self.use_local and self._model:
            try:
                pairs = [(query, c.content) for c in candidates]
                scores = self._model.predict(pairs)
                for c, s in zip(candidates, scores):
                    c.score = float(s)
                candidates.sort(key=lambda x: x.score, reverse=True)
                return candidates
            except Exception as e:
                logger.warning(f"Local reranker execution error: {e}. Using API-based fallback.")

        # API-based Parallel Reranking
        async def score_pair(candidate: RetrievalResult) -> float:
            try:
                criteria = RoutingCriteria(task_type="classification")
                prompt = (
                    f"Rate the relevance of this passage to the query on a scale of 0-10.\n"
                    f"Query: {query}\n"
                    f"Passage: {candidate.content}\n"
                    f"Return only the number."
                )
                res = await llm_client.chat(
                    messages=[ChatMessage(role="user", content=prompt)],
                    criteria=criteria
                )
                # Parse numeric score safely
                import re
                nums = re.findall(r"\d+\.?\d*", res.content)
                if nums:
                    return float(nums[0])
            except Exception as e:
                logger.warning(f"API scoring failed for chunk {candidate.chunk_id}: {e}")
            return 0.0

        scores = await asyncio.gather(*(score_pair(c) for c in candidates))
        for c, s in zip(candidates, scores):
            c.score = s
            
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates
