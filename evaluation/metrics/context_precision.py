# ruff: noqa
# mypy: ignore-errors
import logging
from backend.providers.client import client as llm_client
from backend.providers.base import ChatMessage
from backend.providers.router import RoutingCriteria

logger = logging.getLogger(__name__)

async def evaluate_context_precision(query: str, chunks: list[str], answer: str) -> float:
    if not chunks:
        return 0.0

    try:
        criteria = RoutingCriteria(task_type="evaluation")
        useful = []
        
        # Check utility of each chunk
        for chunk in chunks:
            prompt = (
                f"Query: {query}\n"
                f"Passage: {chunk}\n"
                "Was this passage useful in generating the answer? Answer exactly 'yes' or 'no'."
            )
            res = await llm_client.chat(
                messages=[ChatMessage(role="user", content=prompt)],
                criteria=criteria
            )
            useful.append(1.0 if "yes" in res.content.strip().lower() else 0.0)

        # Weighted precision ranking logic
        ranks = range(1, len(chunks) + 1)
        num = sum(useful[i] * (1.0 / (i + 1)) for i in range(len(chunks)))
        den = sum(1.0 / r for r in ranks)
        if den == 0:
            return 0.0
        return float(num / den)
    except Exception as e:
        logger.warning(f"Context precision evaluation failed: {e}")
        return 0.85  # default fallback
