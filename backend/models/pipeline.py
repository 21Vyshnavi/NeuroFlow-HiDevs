# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
from typing import Any

from pydantic import BaseModel, Extra


class IngestionConfig(BaseModel):
    chunking_strategy: str
    chunk_size_tokens: int
    chunk_overlap_tokens: int
    extractors_enabled: list[str]

    class Config:
        extra = Extra.forbid

class RetrievalConfig(BaseModel):
    dense_k: int
    sparse_k: int
    reranker: str
    top_k_after_rerank: int
    query_expansion: bool
    metadata_filters_enabled: bool

    class Config:
        extra = Extra.forbid

class GenerationConfig(BaseModel):
    model_routing: dict[str, Any]
    max_context_tokens: int
    temperature: float
    system_prompt_variant: str

    class Config:
        extra = Extra.forbid

class EvaluationConfig(BaseModel):
    auto_evaluate: bool
    training_threshold: float

    class Config:
        extra = Extra.forbid

class PipelineConfigModel(BaseModel):
    name: str
    description: str
    ingestion: IngestionConfig
    retrieval: RetrievalConfig
    generation: GenerationConfig
    evaluation: EvaluationConfig

    class Config:
        extra = Extra.forbid
