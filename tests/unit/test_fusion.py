"""
Unit tests for Reciprocal Rank Fusion (RRF).
Uses known inputs and verifies exact expected output ordering and scores.
"""
import pytest
from pipelines.retrieval import RetrievalResult
from pipelines.retrieval.fusion import reciprocal_rank_fusion


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(chunk_id: str, score: float = 0.0) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="doc-1",
        content=f"Content for {chunk_id}",
        score=score,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rrf_single_list():
    """RRF with one list should preserve the original ranking order."""
    results = [_make_result("a"), _make_result("b"), _make_result("c")]
    fused = reciprocal_rank_fusion([results], k=60)
    assert len(fused) == 3
    assert fused[0].chunk_id == "a"
    assert fused[1].chunk_id == "b"
    assert fused[2].chunk_id == "c"


def test_rrf_two_lists_shared_top():
    """A chunk ranked #1 in both lists should appear first after fusion."""
    list_a = [_make_result("x"), _make_result("y"), _make_result("z")]
    list_b = [_make_result("x"), _make_result("z"), _make_result("w")]
    fused = reciprocal_rank_fusion([list_a, list_b], k=60)
    assert fused[0].chunk_id == "x"


def test_rrf_score_formula():
    """Verify RRF score = sum(1 / (k + rank + 1)) for k=60."""
    k = 60
    list_a = [_make_result("a")]
    list_b = [_make_result("a")]
    fused = reciprocal_rank_fusion([list_a, list_b], k=k)
    # rank 0 in both lists → score = 1/(60+0+1) + 1/(60+0+1) = 2/61
    expected = 2.0 / (k + 1)
    assert abs(fused[0].score - expected) < 1e-9


def test_rrf_unique_chunks_merge():
    """Chunks appearing in only one list should still be included."""
    list_a = [_make_result("only-a")]
    list_b = [_make_result("only-b")]
    fused = reciprocal_rank_fusion([list_a, list_b], k=60)
    ids = {r.chunk_id for r in fused}
    assert ids == {"only-a", "only-b"}
    # Equal rank → equal score
    assert fused[0].score == fused[1].score


def test_rrf_empty_lists():
    """RRF with empty input lists should return an empty result."""
    fused = reciprocal_rank_fusion([], k=60)
    assert fused == []


def test_rrf_one_empty_one_full():
    """One empty list and one populated list should return the populated results."""
    results = [_make_result("a"), _make_result("b")]
    fused = reciprocal_rank_fusion([[], results], k=60)
    assert len(fused) == 2


def test_rrf_custom_k():
    """Different k value should change the scores."""
    fused_60 = reciprocal_rank_fusion([[_make_result("a")]], k=60)
    fused_10 = reciprocal_rank_fusion([[_make_result("a")]], k=10)
    # k=10 → 1/11, k=60 → 1/61; smaller k gives higher scores
    assert fused_10[0].score > fused_60[0].score


def test_rrf_preserves_content():
    """Fused results should preserve the original content field."""
    results = [_make_result("alpha")]
    fused = reciprocal_rank_fusion([results], k=60)
    assert fused[0].content == "Content for alpha"
    assert fused[0].document_id == "doc-1"
