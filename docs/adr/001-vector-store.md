# ADR-001: Vector Store — pgvector over Pinecone, Weaviate, or Qdrant

**Status:** Accepted
**Date:** 2026-07-02

## Context

NeuroFlow needs a vector store for chunk embeddings that supports approximate nearest-neighbor
search at the scale of a mid-size RAG deployment (target: low millions of chunks in year one),
alongside metadata filtering and, critically, joins against relational data — documents,
generations, evaluations, and fine-tuning records all need to correlate with the chunks that
produced them.

Candidates evaluated:
- **Pinecone** — fully managed, purpose-built ANN service, strong at very large scale, but
  introduces a second system of record (data lives outside Postgres), adds network hops for every
  retrieval, and adds a recurring managed-service cost independent of our existing Postgres spend.
- **Weaviate** — feature-rich (hybrid search, modules), but another separate service to operate,
  with its own backup/HA story and a steeper operational learning curve for a small early-stage
  team.
- **Qdrant** — lightweight, good performance, but still a separate datastore with its own
  consistency model relative to Postgres; joining vector results back to relational metadata
  (documents, evaluations) requires app-level stitching or duplicated metadata.
- **pgvector** — a Postgres extension; vectors live in the same database as documents, chunks,
  generations, and evaluations.

## Decision

Use **pgvector** as the vector store, embedded in the same Postgres instance that holds all other
NeuroFlow relational data.

Rationale:
1. **Single system of record.** Retrieval needs metadata filtering (`document_id`, tags, date
   ranges) combined with vector search. In pgvector this is a single SQL query with a `WHERE`
   clause; in a separate vector DB it's two round trips or duplicated metadata that can drift.
2. **Operational simplicity.** One database to back up, monitor, scale, and secure instead of two.
   For a team building 19 more tasks on top of this architecture, operational surface area is a
   real cost.
3. **Transactional consistency.** Ingestion writes a document, its chunks, and their embeddings in
   one transaction. A separate vector store makes "document ready" an eventually-consistent,
   two-system state instead of a single commit.
4. **Good-enough scale for the target range.** HNSW indexing in pgvector handles low-millions of
   vectors with acceptable p99 latency for our use case; we are not (yet) at the scale where a
   purpose-built ANN service's extra throughput matters more than the above benefits.
5. **Cost.** No separate managed-service bill; scales with the Postgres instance we already need.

## Consequences

**Positive:**
- Simpler mental model, fewer moving parts, faster to build the first 19 tasks on.
- Metadata-filtered vector search is trivial and consistent.
- Easier local development (one `docker-compose` service, not two).

**Negative:**
- pgvector's ANN performance and recall/latency tradeoffs are weaker than purpose-built vector
  databases at very large scale (tens of millions+ of vectors) or very high QPS.
- Index build/maintenance (HNSW) competes for resources with the rest of the relational workload
  on the same instance; requires careful `maintenance_work_mem` tuning and monitoring as chunk
  volume grows.
- Horizontal scaling of the vector workload independent of the relational workload is not
  possible without introducing read replicas or eventually migrating.

## Revisit trigger

If chunk volume exceeds ~20M vectors, or p99 retrieval latency regularly exceeds our SLO after
index tuning, re-evaluate a dedicated vector store (Qdrant is the most likely next candidate given
its lighter operational footprint relative to Pinecone/Weaviate) and plan a migration that keeps
metadata in Postgres with vector IDs as the join key.
