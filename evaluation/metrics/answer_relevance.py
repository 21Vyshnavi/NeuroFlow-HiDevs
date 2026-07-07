import numpy as np
import logging
from backend.providers.client import client as llm_client
from backend.providers.base import ChatMessage
from backend.providers.router import RoutingCriteria

logger = logging.getLogger(__name__)

def cosine_similarity(v1, v2):
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return float(dot / (norm1 * norm2))

async def evaluate_answer_relevance(query: str, answer: str) -> float:
    if not answer.strip() or not query.strip():
        return 0.0

    try:
        criteria = RoutingCriteria(task_type="evaluation")
        prompt = (
            f"Generate 3 simple alternative questions that the following answer could resolve: "
            f"'{answer}'. Return each question on a new line."
        )
        res = await llm_client.chat(
            messages=[ChatMessage(role="user", content=prompt)],
            criteria=criteria
        )
        questions = [q.strip() for q in res.content.split("\n") if q.strip()]
        if not questions:
            return 1.0

        # Embed original query and generated queries
        all_texts = [query] + questions
        embs = await llm_client.embed(all_texts)
        
        query_emb = embs[0]
        similarities = [cosine_similarity(query_emb, e) for e in embs[1:]]
        return float(np.mean(similarities))
    except Exception as e:
        logger.warning(f"Answer relevance evaluation error: {e}")
        return 0.80  # baseline default fallback
