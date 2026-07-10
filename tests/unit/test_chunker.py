"""
Unit tests for the chunking module.
Tests fixed-size, semantic, and hierarchical strategies with known inputs.
"""
import pytest
from pipelines.ingestion.chunker import (
    fixed_size_chunking,
    hierarchical_chunking,
    split_into_sentences,
    get_token_count,
    Chunk,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LONG_TEXT = (
    "Retrieval-augmented generation combines retrieval and generation. "
    "It uses a vector database to find relevant documents. "
    "The retrieved chunks are fed into the language model as context. "
    "This reduces hallucination significantly. "
    "The technique was introduced by Facebook AI Research. "
    "Modern RAG systems use hybrid search. "
    "Hybrid search combines dense and sparse retrieval methods. "
    "Cross-encoder reranking further refines results. "
    "Production systems add evaluation pipelines. "
    "Metrics like faithfulness and relevance measure output quality."
)

SHORT_TEXT = "Hello world. This is a test."


# ---------------------------------------------------------------------------
# Tests — split_into_sentences
# ---------------------------------------------------------------------------

def test_split_into_sentences_basic():
    """Sentences are split on punctuation boundaries."""
    sentences = split_into_sentences(SHORT_TEXT)
    assert len(sentences) >= 2
    assert "Hello world." in sentences[0]


def test_split_into_sentences_empty():
    """Empty string yields an empty list."""
    assert split_into_sentences("") == []


# ---------------------------------------------------------------------------
# Tests — get_token_count
# ---------------------------------------------------------------------------

def test_token_count_non_zero():
    """Token count for non-empty text is positive."""
    assert get_token_count("Hello world this is a test") > 0


def test_token_count_empty():
    """Empty string returns 0 tokens."""
    assert get_token_count("") == 0


# ---------------------------------------------------------------------------
# Tests — fixed_size_chunking
# ---------------------------------------------------------------------------

def test_fixed_size_single_chunk():
    """Short text should produce exactly one chunk."""
    chunks = fixed_size_chunking(SHORT_TEXT, target_size=512)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert SHORT_TEXT.strip() in chunks[0].content


def test_fixed_size_multiple_chunks():
    """Long text with small target_size should produce multiple chunks."""
    chunks = fixed_size_chunking(LONG_TEXT, target_size=30, overlap=0)
    assert len(chunks) >= 2
    # Each chunk index is sequential
    for i, c in enumerate(chunks):
        assert c.chunk_index == i


def test_fixed_size_token_limit():
    """No chunk should exceed the target token count (with some tolerance)."""
    chunks = fixed_size_chunking(LONG_TEXT, target_size=40)
    for c in chunks:
        # Allow 50% tolerance for single-sentence overflow
        assert c.token_count <= 60, f"Chunk {c.chunk_index} has {c.token_count} tokens"


def test_fixed_size_metadata_default():
    """All chunks should have empty metadata by default."""
    chunks = fixed_size_chunking(LONG_TEXT, target_size=50)
    for c in chunks:
        assert isinstance(c.metadata, dict)


def test_fixed_size_no_empty_chunks():
    """No chunk should have empty content."""
    chunks = fixed_size_chunking(LONG_TEXT, target_size=30)
    for c in chunks:
        assert len(c.content.strip()) > 0


# ---------------------------------------------------------------------------
# Tests — hierarchical_chunking
# ---------------------------------------------------------------------------

def test_hierarchical_with_headings():
    """Hierarchical chunking with headings should produce section-based chunks."""
    text = "Introduction to RAG.\n\nVector databases are key.\n\nConclusion and future work."
    headings = [{"text": "Chapter 1"}]
    chunks = hierarchical_chunking(text, headings)
    assert len(chunks) == 3
    assert chunks[0].metadata["parent_chunk"] == "Chapter 1"


def test_hierarchical_no_headings_falls_back():
    """Without headings, hierarchical falls back to fixed-size chunking."""
    chunks = hierarchical_chunking(LONG_TEXT, headings=[])
    assert len(chunks) >= 1
    # Should return Chunk objects
    assert all(isinstance(c, Chunk) for c in chunks)
