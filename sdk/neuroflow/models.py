from pydantic import BaseModel, ConfigDict
from typing import Optional, Any

class Document(BaseModel):
    id: str
    filename: str
    status: str
    pipeline_id: Optional[str] = None
    
    model_config = ConfigDict(extra="ignore")

class QueryResult(BaseModel):
    answer: str
    sources: list[dict[str, Any]] = []
    
    model_config = ConfigDict(extra="ignore")

class EvaluationResult(BaseModel):
    run_id: str
    faithfulness: float
    answer_relevance: float
    context_precision: float
    context_recall: float
    
    model_config = ConfigDict(extra="ignore")
