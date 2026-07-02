# ADR-002: Chunking Strategy — fixed-size vs. sentence-boundary vs. semantic

**Status:** Accepted
**Date:** 2026-07-02

## Context

Chunking directly determines retrieval quality: chunks too large dilute embedding relevance and
waste context budget; chunks too small lose surrounding context needed for faithful answers.
Three strategies were compared:

- **Fixed-size chunking** — split every N tokens, with overlap. Cheap, deterministic, fast. But
  it cuts sentences and ideas in half indiscriminately, which hurts both embedding quality and
  the coherence of what the generator receives.
- **Sentence-boundary chunking** — split on sentence boundaries, accumulating sentences up to a
  target token budget with overlap. Preserves grammatical/semantic units, cheap to compute
  (no model inference required), and produces predictable chunk sizes.
- **Semantic chunking** — use embedding similarity between adjacent sentences/paragraphs to find
  natural topic-shift boundaries, producing variable-length, topically coherent chunks. Higher
  retrieval quality on long, loosely structured documents, but requires an embedding pass over the
  document purely to determine boundaries — meaningfully more compute and latency per document
  than the other two strategies.

## Decision

Default to **sentence-boundary chunking** (512-token target, 15% overlap) for all ingestion.

Switch to **semantic chunking** per-pipeline when:
1. The source documents are long-form and loosely structured (e.g. research reports, meeting
   transcripts, narrative documents) where topic shifts don't align with fixed sentence-count
   windows, **and**
2. The pipeline's retrieval quality metrics (context precision/recall from the Evaluation
   Subsystem) show sentence-boundary chunking underperforming on that document type — this is a
   measured decision per pipeline, not a blanket policy.

Do **not** use fixed-size chunking as a default. It remains available as a fallback for content
where sentence segmentation fails (e.g. malformed OCR output, code files, tabular CSV rows) where
"sentence" isn't a meaningful unit anyway.

## Consequences

**Positive:**
- Sentence-boundary chunking is fast, deterministic, and requires no extra model calls at
  ingestion time — keeps ingestion latency and cost predictable and low by default.
- Chunk boundaries respect grammatical units, meaningfully better than fixed-size for both
  embedding quality and generator readability.
- Semantic chunking is available as an opt-in upgrade, gated by actual measured retrieval quality
  rather than assumed — avoids paying its compute cost where it wouldn't move the needle.

**Negative:**
- Sentence-boundary chunking can still separate related ideas that span multiple paragraphs
  (e.g. a claim and its supporting evidence three paragraphs later) — mitigated by the 15%
  overlap and by cross-encoder reranking downstream, but not eliminated.
- Running two chunking code paths (sentence-boundary + semantic) adds implementation and testing
  surface area versus a single fixed strategy.
- The switch condition ("measured underperformance") requires the Evaluation Subsystem to be live
  before it can be acted on — meaning the earliest pipelines will run on sentence-boundary
  chunking by default until enough evaluation data accumulates to justify a change.

## Revisit trigger

Per-pipeline: if `context_precision` or `context_recall` rolling 7-day average falls below 0.65
for a pipeline whose source documents are long-form/unstructured, evaluate switching that
pipeline's `chunking_strategy` to `semantic`.
