# ruff: noqa
# mypy: ignore-errors
from typing import List, Dict
from pipelines.retrieval import RetrievalResult

def reciprocal_rank_fusion(
    result_lists: List[List[RetrievalResult]],
    k: int = 60
) -> List[RetrievalResult]:
    rrf_scores: Dict[str, float] = {}
    chunk_map: Dict[str, RetrievalResult] = {}

    for result_list in result_lists:
        for rank, res in enumerate(result_list):
            chunk_map[res.chunk_id] = res
            score = 1.0 / (k + rank + 1)
            rrf_scores[res.chunk_id] = rrf_scores.get(res.chunk_id, 0.0) + score

    # Sort chunks by final RRF score descending
    sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
    
    fused_results = []
    for cid in sorted_chunk_ids:
        res = chunk_map[cid]
        res.score = rrf_scores[cid]
        fused_results.append(res)
        
    return fused_results
