# ruff: noqa
# mypy: ignore-errors
import logging
from pydantic import BaseModel
from typing import List, Dict, Any
from backend.providers.client import client as llm_client
from backend.providers.base import ChatMessage
from backend.providers.router import RoutingCriteria

logger = logging.getLogger(__name__)

class ProcessedQuery(BaseModel):
    original_query: str
    expanded_queries: List[str]
    metadata_filters: Dict[str, Any]
    query_type: str  # "factual" | "analytical" | "comparative" | "procedural"

async def process_query(query: str) -> ProcessedQuery:
    expanded = []
    metadata_filters = {}
    query_type = "factual"

    # Query Expansion & Parameter Extraction (implicit fallback)
    try:
        criteria = RoutingCriteria(task_type="classification")
        prompt = (
            f"Given the user query: '{query}', return a JSON object with: "
            "1. 'expanded': list of 2 alternative phrasings. "
            "2. 'filters': dict of implicit filters (e.g., year, topic). "
            "3. 'type': one of ['factual', 'analytical', 'comparative', 'procedural']. "
            "Return only the valid raw JSON."
        )
        res = await llm_client.chat(
            messages=[ChatMessage(role="user", content=prompt)],
            criteria=criteria
        )
        # Parse output safely
        import json
        import re
        content = res.content.strip()
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            expanded = parsed.get("expanded", [])
            metadata_filters = parsed.get("filters", {})
            query_type = parsed.get("type", "factual")
    except Exception as e:
        logger.warning(f"Failed to use LLM query expansion/filter: {e}")
        # Manual fallback parsers
        expanded = [f"explain {query}", f"details on {query}"]
        if "2023" in query:
            metadata_filters["year"] = 2023
        if "climate" in query.lower():
            metadata_filters["topic"] = "climate"

    return ProcessedQuery(
        original_query=query,
        expanded_queries=expanded,
        metadata_filters=metadata_filters,
        query_type=query_type
    )
