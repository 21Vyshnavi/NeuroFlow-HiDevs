"""
Unit tests for PipelineConfigModel Pydantic validation.
Verifies that valid configs pass and invalid configs are rejected.
"""
import pytest
from pydantic import ValidationError
from backend.models.pipeline import (
    PipelineConfigModel,
    IngestionConfig,
    RetrievalConfig,
    GenerationConfig,
    EvaluationConfig,
)


# ---------------------------------------------------------------------------
# Fixture — valid config dict
# ---------------------------------------------------------------------------

def _valid_config() -> dict:
    """Return a fully valid pipeline configuration dict."""
    return {
        "name": "production-v2",
        "description": "Production pipeline with hybrid search and GPT-4o",
        "ingestion": {
            "chunking_strategy": "fixed_size",
            "chunk_size_tokens": 512,
            "chunk_overlap_tokens": 64,
            "extractors_enabled": ["pdf", "docx", "image"],
        },
        "retrieval": {
            "dense_k": 20,
            "sparse_k": 20,
            "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "top_k_after_rerank": 5,
            "query_expansion": True,
            "metadata_filters_enabled": True,
        },
        "generation": {
            "model_routing": {"primary": "gpt-4o", "fallback": "gpt-4o-mini"},
            "max_context_tokens": 4096,
            "temperature": 0.3,
            "system_prompt_variant": "concise",
        },
        "evaluation": {
            "auto_evaluate": True,
            "training_threshold": 0.85,
        },
    }


# ---------------------------------------------------------------------------
# Tests — valid configs
# ---------------------------------------------------------------------------

def test_valid_config_accepted():
    """A fully valid config should parse without errors."""
    config = PipelineConfigModel(**_valid_config())
    assert config.name == "production-v2"
    assert config.ingestion.chunk_size_tokens == 512
    assert config.retrieval.dense_k == 20
    assert config.generation.temperature == 0.3
    assert config.evaluation.auto_evaluate is True


def test_valid_config_all_fields_present():
    """All nested config sections should be populated."""
    config = PipelineConfigModel(**_valid_config())
    assert isinstance(config.ingestion, IngestionConfig)
    assert isinstance(config.retrieval, RetrievalConfig)
    assert isinstance(config.generation, GenerationConfig)
    assert isinstance(config.evaluation, EvaluationConfig)


# ---------------------------------------------------------------------------
# Tests — missing required fields
# ---------------------------------------------------------------------------

def test_missing_name_rejected():
    """Config without 'name' should be rejected."""
    cfg = _valid_config()
    del cfg["name"]
    with pytest.raises(ValidationError) as exc_info:
        PipelineConfigModel(**cfg)
    assert "name" in str(exc_info.value)


def test_missing_ingestion_rejected():
    """Config without 'ingestion' section should be rejected."""
    cfg = _valid_config()
    del cfg["ingestion"]
    with pytest.raises(ValidationError):
        PipelineConfigModel(**cfg)


def test_missing_retrieval_field_rejected():
    """Missing a required field inside retrieval should be rejected."""
    cfg = _valid_config()
    del cfg["retrieval"]["reranker"]
    with pytest.raises(ValidationError):
        PipelineConfigModel(**cfg)


# ---------------------------------------------------------------------------
# Tests — wrong types
# ---------------------------------------------------------------------------

def test_wrong_type_temperature():
    """Temperature as a string should be coerced or rejected."""
    cfg = _valid_config()
    cfg["generation"]["temperature"] = "not-a-float"
    with pytest.raises(ValidationError):
        PipelineConfigModel(**cfg)


def test_wrong_type_chunk_size():
    """chunk_size_tokens as a string should be rejected."""
    cfg = _valid_config()
    cfg["ingestion"]["chunk_size_tokens"] = "big"
    with pytest.raises(ValidationError):
        PipelineConfigModel(**cfg)


# ---------------------------------------------------------------------------
# Tests — extra fields rejected (extra=forbid)
# ---------------------------------------------------------------------------

def test_extra_top_level_field_rejected():
    """Extra fields at the top level should be rejected."""
    cfg = _valid_config()
    cfg["unknown_field"] = "surprise"
    with pytest.raises(ValidationError):
        PipelineConfigModel(**cfg)


def test_extra_nested_field_rejected():
    """Extra fields inside a nested config should be rejected."""
    cfg = _valid_config()
    cfg["ingestion"]["bogus_key"] = True
    with pytest.raises(ValidationError):
        PipelineConfigModel(**cfg)


# ---------------------------------------------------------------------------
# Tests — edge cases
# ---------------------------------------------------------------------------

def test_zero_temperature_valid():
    """Temperature of 0.0 should be valid."""
    cfg = _valid_config()
    cfg["generation"]["temperature"] = 0.0
    config = PipelineConfigModel(**cfg)
    assert config.generation.temperature == 0.0


def test_empty_extractors_list_valid():
    """An empty extractors list should be accepted."""
    cfg = _valid_config()
    cfg["ingestion"]["extractors_enabled"] = []
    config = PipelineConfigModel(**cfg)
    assert config.ingestion.extractors_enabled == []
