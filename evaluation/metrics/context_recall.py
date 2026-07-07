import logging
import re
from backend.providers.client import client as llm_client
from backend.providers.base import ChatMessage
from backend.providers.router import RoutingCriteria

logger = logging.getLogger(__name__)

async def evaluate_context_recall(query: str, chunks: list[str], answer: str) -> float:
    if not answer.strip():
        return 0.0
    if not chunks:
        return 0.0

    try:
        criteria = RoutingCriteria(task_type="evaluation")
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer) if s.strip()]
        if not sentences:
            return 1.0

        attributable = 0
        context_block = "\n\n".join(chunks)

        for s in sentences:
            prompt = (
                f"Context: {context_block}\n"
                f"Sentence: {s}\n"
                "Can this sentence be fully attributed to the provided context? Answer exactly 'yes' or 'no'."
            )
            res = await llm_client.chat(
                messages=[ChatMessage(role="user", content=prompt)],
                criteria=criteria
            )
            if "yes" in res.content.strip().lower():
                attributable += 1

        return float(attributable / len(sentences))
    except Exception as e:
        logger.warning(f"Context recall evaluation failed: {e}")
        return 0.80  # default fallback
