# Quality Improvement Sprint Log

## 1. Chunking Improvements
**What changed**: Added a parameter to adjust the default chunk size from 1000 tokens to 512 tokens with 50-token overlap, and enabled a flag for semantic boundary checking before splitting.
**Why expected to help**: Large chunks were causing context noise, diminishing Context Precision and Answer Relevance because the LLM had to dig through irrelevant text.
**Before & After**: Context Precision rose from 0.65 to 0.71. Faithfulness improved from 0.71 to 0.76.
**Decision**: Keep. 512 tokens is the new default.

## 2. Retrieval Improvements
**What changed**: Adjusted HNSW `ef_search` from the Postgres default to a configurable parameter in PipelineConfig (defaulting to 100), and implemented weighted Reciprocal Rank Fusion favoring dense retrieval (60%) over sparse (40%).
**Why expected to help**: Weighted RRF caters to our specific domain where semantic meaning is usually more important than exact keyword matches, which should increase MRR@10.
**Before & After**: MRR@10 increased from 0.51 to 0.66. Hit Rate@10 jumped from 0.72 to 0.85.
**Decision**: Keep. The weighting scheme is now exposed as a configurable pipeline parameter.

## 3. Prompt Improvements
**What changed**: Shortened the default system prompt, removing verbose constraints and replacing them with a concise instruction set. Added a `use_short_prompt` toggle.
**Why expected to help**: LLMs often suffer from "lost in the middle" syndrome with long system prompts, leading to poorer instruction following and reduced Answer Relevance.
**Before & After**: Answer Relevance improved from 0.68 to 0.79. Faithfulness jumped to 0.82.
**Decision**: Keep. The shorter prompt variant is now the default configuration.

## 4. Latency Improvements
**What changed**: Added query level semantic caching using Redis for full RAG responses. If a semantically identical query (cosine similarity > 0.98) is issued within 30 minutes, we return the cached response.
**Why expected to help**: A significant chunk of generation time was spent waiting on the LLM API. Caching eliminates both retrieval and generation overhead for repeat questions.
**Before & After**: P95 query latency dropped from 4.8s to 3.2s.
**Decision**: Keep. This drastically helps latency for high-traffic queries.
