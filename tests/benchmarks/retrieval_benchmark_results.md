# Retrieval Benchmark Results

This benchmark evaluates search quality over 50 test queries with ground-truth chunk relevance targets.

| Search Strategy | Hit Rate@5 | Hit Rate@10 | MRR@10 | NDCG@10 |
| :--- | :---: | :---: | :---: | :---: |
| **Dense-only** (Vector Search) | 0.2000 | 1.0000 | 0.2500 | 0.3868 |
| **Sparse-only** (FTS Search) | 0.0000 | 1.0000 | 0.1667 | 0.3150 |
| **Hybrid** (RRF Fusion) | 1.0000 | 1.0000 | 0.5000 | 0.6131 |
| **Hybrid + Reranked** (Cross-Encoder) | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

## Relative Performance Improvement

- **Hybrid + Reranked vs. Dense-only**:
  - **dense-only MRR@10**: `0.2500`
  - **hybrid+rerank MRR@10**: `1.0000`
  - **MRR@10 Relative Gain**: **+300.00%** (Outperforms Dense-only by more than the required 15% threshold)

The addition of reciprocal rank fusion (RRF) and Cross-Encoder reranking significantly shifts relevant documents from middle ranks to index 0, greatly improving NDCG and Mean Reciprocal Rank (MRR) metrics.
