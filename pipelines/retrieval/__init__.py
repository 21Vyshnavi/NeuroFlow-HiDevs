# ruff: noqa
# mypy: ignore-errors
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    rank: Optional[int] = None
    metadata: Dict[str, Any] = {}
