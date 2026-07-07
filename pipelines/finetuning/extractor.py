import re
import json
import logging
from typing import List, Dict, Any
from backend.db.pool import db_pool

logger = logging.getLogger(__name__)

# Regex for PII detection
PII_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PII_PHONE = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")

def validate_pair(pair: Dict[str, Any]) -> bool:
    content = pair.get("assistant_message", "")
    query = pair.get("user_message", "")

    # Token/Length constraints
    word_count = len(content.split())
    if word_count < 10 or word_count > 2000:
        return False

    # Citation present check [Source N]
    if not re.search(r"\[Source \d+\]", content):
        return False

    # PII Checks
    if PII_EMAIL.search(query) or PII_PHONE.search(query):
        return False
    if PII_EMAIL.search(content) or PII_PHONE.search(content):
        return False

    return True

async def extract_training_pairs(quality_threshold: float = 0.82) -> List[Dict[str, Any]]:
    pool = db_pool.get_pool()
    if not pool:
        return []

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT tp.id, tp.run_id, tp.system_prompt, tp.user_message, tp.assistant_message, tp.quality_score
            FROM training_pairs tp
            JOIN pipeline_runs pr ON tp.run_id = pr.id
            LEFT JOIN evaluations e ON pr.id = e.run_id
            WHERE tp.quality_score >= $1
              AND tp.included_in_job IS NULL
              AND (e.user_rating >= 4 OR e.user_rating IS NULL)
            """,
            quality_threshold
        )
        
        valid_pairs = []
        for r in rows:
            p = {
                "id": str(r["id"]),
                "run_id": str(r["run_id"]),
                "system_prompt": r["system_prompt"] or "You are a precise research assistant.",
                "user_message": r["user_message"],
                "assistant_message": r["assistant_message"],
                "quality_score": float(r["quality_score"])
            }
            if validate_pair(p):
                valid_pairs.append(p)
                
        return valid_pairs
