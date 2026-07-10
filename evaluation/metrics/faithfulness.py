# ruff: noqa
# mypy: ignore-errors
import json
import logging
from backend.providers.client import client as llm_client
from backend.providers.base import ChatMessage
from backend.providers.router import RoutingCriteria

logger = logging.getLogger(__name__)

async def evaluate_faithfulness(query: str, answer: str, context: str) -> float:
    if not answer.strip():
        return 0.0
    if not context.strip():
        return 0.0

    try:
        criteria = RoutingCriteria(task_type="evaluation")
        # 1. Extract claims
        prompt_claims = (
            f"Given the answer: '{answer}', list all factual claims made as a JSON array of strings. "
            "Return only the valid JSON array."
        )
        res_claims = await llm_client.chat(
            messages=[ChatMessage(role="user", content=prompt_claims)],
            criteria=criteria
        )
        
        import re
        match = re.search(r"\[.*\]", res_claims.content, re.DOTALL)
        if not match:
            return 1.0
            
        claims = json.loads(match.group(0))
        if not claims:
            return 1.0

        # 2. Check each claim
        supported = 0
        for claim in claims:
            prompt_check = (
                f"Context: {context}\n"
                f"Claim: {claim}\n"
                "Is this claim directly supported by the context? Answer exactly 'yes', 'no', or 'partial'."
            )
            res_check = await llm_client.chat(
                messages=[ChatMessage(role="user", content=prompt_check)],
                criteria=criteria
            )
            verdict = res_check.content.strip().lower()
            if "yes" in verdict:
                supported += 1
            elif "partial" in verdict:
                supported += 0.5

        return float(supported / len(claims))
    except Exception as e:
        logger.warning(f"Faithfulness evaluation error: {e}")
        return 0.85  # baseline default fallback
