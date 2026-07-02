# NeuroFlow API Contracts

All endpoints are versioned under `/v1`. This document is the contract implementation must follow;
any breaking change requires a version bump, not an in-place edit.

## Conventions

- **Base URL:** `https://api.neuroflow.dev/v1`
- **Auth:** Bearer token (`Authorization: Bearer <api_key>`) unless noted otherwise. API keys are
  scoped per workspace and carry a role (`admin`, `write`, `read`).
- **Content type:** `application/json` unless a `multipart/form-data` upload is noted.
- **Errors:** all error responses share this envelope:

```json
{
  "error": {
    "code": "string (machine-readable)",
    "message": "string (human-readable)",
    "request_id": "uuid"
  }
}
```

- **Common error codes** (apply to every endpoint unless overridden):

| HTTP | code | meaning |
|---|---|---|
| 400 | `invalid_request` | Malformed body / missing required field |
| 401 | `unauthorized` | Missing or invalid API key |
| 403 | `forbidden` | Valid key, insufficient role/scope |
| 404 | `not_found` | Resource does not exist or not visible to this workspace |
| 409 | `conflict` | Duplicate resource / state conflict |
| 422 | `unprocessable` | Well-formed but semantically invalid (e.g. unsupported file type) |
| 429 | `rate_limited` | Rate limit exceeded; see `Retry-After` header |
| 500 | `internal_error` | Unexpected server error |
| 503 | `service_unavailable` | Downstream dependency (LLM provider, vector store) unavailable |

---

## `POST /ingest`

Accepts a file or a URL for ingestion.

**Auth:** required, role `write`
**Rate limit:** 30 requests/min per API key; 200MB max file size

**Request:** `multipart/form-data` (for file) or `application/json` (for URL)

File form fields:
| field | type | required |
|---|---|---|
| `file` | binary | yes (if no `url`) |
| `pipeline_id` | string | no (defaults to workspace default pipeline) |
| `metadata` | JSON string | no |

URL JSON body:
```json
{
  "url": "https://example.com/doc",
  "pipeline_id": "pipeline_abc123",
  "metadata": { "tags": ["policy", "2026"] }
}
```

**Response `202 Accepted`:**
```json
{
  "document_id": "doc_9f2a...",
  "status": "pending",
  "source_type": "pdf",
  "created_at": "2026-07-02T10:00:00Z"
}
```

**Errors:** `400 invalid_request` (no file/url), `422 unprocessable` (unsupported modality),
`413 payload_too_large` (file exceeds size limit), `429 rate_limited`.

---

## `POST /query`

Executes a RAG query: retrieval + generation.

**Auth:** required, role `read` (generation billing may require `write`, per workspace policy)
**Rate limit:** 60 requests/min per API key

**Request:**
```json
{
  "query": "What is our refund policy for enterprise customers?",
  "pipeline_id": "pipeline_abc123",
  "filters": { "document_id": null, "tags": ["policy"], "date_from": null, "date_to": null },
  "top_k": 8,
  "model_override": null,
  "stream": true
}
```

**Response `200 OK`** (non-streaming case, `stream: false`):
```json
{
  "query_id": "qry_7bd1...",
  "answer": "Enterprise customers are eligible for a full refund within 30 days...",
  "model_used": "gpt-4.1-mini",
  "context": [
    { "chunk_id": "chk_001", "document_id": "doc_9f2a", "score": 0.83, "text": "..." }
  ],
  "latency_ms": 1120,
  "created_at": "2026-07-02T10:01:00Z"
}
```

**Response `202 Accepted`** (streaming case, `stream: true`): returns `query_id` immediately;
client connects to `GET /query/{query_id}/stream` for tokens.
```json
{ "query_id": "qry_7bd1...", "status": "streaming" }
```

**Errors:** `400 invalid_request`, `404 not_found` (`pipeline_id` unknown), `422 unprocessable`
(empty query), `429 rate_limited`, `503 service_unavailable` (LLM provider down — response
includes `retry_after_ms`).

---

## `GET /query/{query_id}/stream`

Server-Sent Events stream of the generation for a query started with `stream: true`.

**Auth:** required, role `read`
**Rate limit:** shares budget with `/query`; 1 open stream per `query_id`

**Response:** `Content-Type: text/event-stream`. Event frames:
```
event: token
data: {"delta": "Enterprise "}

event: token
data: {"delta": "customers "}

event: citation
data: {"chunk_id": "chk_001", "document_id": "doc_9f2a"}

event: done
data: {"query_id": "qry_7bd1...", "model_used": "gpt-4.1-mini", "latency_ms": 1120, "finish_reason": "stop"}
```

**Errors:** `404 not_found` (unknown/expired `query_id`), `409 conflict` (stream already
consumed or not yet started — retry shortly).

---

## `GET /evaluations`

Paginated evaluation results.

**Auth:** required, role `read`
**Rate limit:** 120 requests/min per API key

**Query params:** `pipeline_id`, `model`, `min_faithfulness`, `date_from`, `date_to`,
`cursor`, `limit` (default 50, max 200)

**Response `200 OK`:**
```json
{
  "data": [
    {
      "evaluation_id": "eval_001",
      "generation_id": "gen_001",
      "query_id": "qry_7bd1...",
      "faithfulness": 0.91,
      "answer_relevance": 0.88,
      "context_precision": 0.76,
      "context_recall": 0.82,
      "user_rating": 5,
      "model_used": "gpt-4.1-mini",
      "created_at": "2026-07-02T10:01:05Z"
    }
  ],
  "next_cursor": "eyJvZmZzZXQiOjUwfQ==",
  "has_more": true
}
```

**Errors:** `400 invalid_request` (bad cursor/limit).

---

## `GET /evaluations/aggregate`

Rolling quality metrics.

**Auth:** required, role `read`
**Rate limit:** 60 requests/min per API key

**Query params:** `pipeline_id` (optional), `model` (optional), `window` (`1h` | `24h` | `7d`,
default `24h`)

**Response `200 OK`:**
```json
{
  "window": "24h",
  "pipeline_id": "pipeline_abc123",
  "sample_count": 4213,
  "metrics": {
    "faithfulness": { "mean": 0.87, "p50": 0.90, "p10": 0.61 },
    "answer_relevance": { "mean": 0.84, "p50": 0.88, "p10": 0.55 },
    "context_precision": { "mean": 0.72, "p50": 0.75, "p10": 0.40 },
    "context_recall": { "mean": 0.79, "p50": 0.82, "p10": 0.48 }
  },
  "computed_at": "2026-07-02T10:15:00Z"
}
```

**Errors:** `400 invalid_request` (invalid `window` value).

---

## `POST /pipelines`

Creates a named pipeline configuration (embedding model, chunking strategy, reranker, default
generation model tier, etc.).

**Auth:** required, role `admin`
**Rate limit:** 10 requests/min per API key

**Request:**
```json
{
  "name": "support-docs-v2",
  "embedding_model": "text-embedding-3-large",
  "chunking": { "strategy": "sentence_boundary", "chunk_size": 512, "overlap_pct": 15 },
  "reranker": "bge-reranker-large",
  "default_model_tier": "balanced",
  "retrieval": { "top_k_vector": 50, "top_k_keyword": 50, "rrf_k": 60, "final_top_n": 8 }
}
```

**Response `201 Created`:**
```json
{
  "pipeline_id": "pipeline_abc123",
  "name": "support-docs-v2",
  "created_at": "2026-07-02T10:20:00Z"
}
```

**Errors:** `400 invalid_request`, `409 conflict` (name already exists in workspace),
`422 unprocessable` (invalid chunking/reranker combination).

---

## `GET /pipelines/{id}/runs`

Pipeline execution history (ingestion runs, retrieval configs used, etc.).

**Auth:** required, role `read`
**Rate limit:** 60 requests/min per API key

**Query params:** `cursor`, `limit` (default 50, max 200), `status` (`pending`|`success`|`failed`)

**Response `200 OK`:**
```json
{
  "data": [
    {
      "run_id": "run_001",
      "pipeline_id": "pipeline_abc123",
      "type": "ingest",
      "status": "success",
      "document_count": 12,
      "started_at": "2026-07-02T09:00:00Z",
      "finished_at": "2026-07-02T09:02:30Z"
    }
  ],
  "next_cursor": null,
  "has_more": false
}
```

**Errors:** `404 not_found` (unknown `pipeline_id`).

---

## `POST /finetune/jobs`

Submits a fine-tuning job built from qualifying evaluation-log examples.

**Auth:** required, role `admin`
**Rate limit:** 5 requests/min per API key

**Request:**
```json
{
  "base_model": "gpt-4.1-mini",
  "pipeline_id": "pipeline_abc123",
  "filter": { "min_faithfulness": 0.8, "min_user_rating": 4, "date_from": "2026-06-01" },
  "hyperparameters": { "n_epochs": 3, "learning_rate_multiplier": 1.0 },
  "experiment_name": "support-docs-ft-v3"
}
```

**Response `202 Accepted`:**
```json
{
  "job_id": "ft_job_001",
  "status": "queued",
  "training_example_count": 1840,
  "mlflow_run_id": "run_abcdef",
  "created_at": "2026-07-02T10:30:00Z"
}
```

**Errors:** `400 invalid_request`, `422 unprocessable` (fewer than minimum required examples,
default threshold 50), `409 conflict` (an identical job is already running for this pipeline).

---

## `GET /finetune/jobs/{id}`

Job status and metrics.

**Auth:** required, role `read`
**Rate limit:** 120 requests/min per API key

**Response `200 OK`:**
```json
{
  "job_id": "ft_job_001",
  "status": "succeeded",
  "base_model": "gpt-4.1-mini",
  "fine_tuned_model": "ft:gpt-4.1-mini:neuroflow:support-docs-v3:abc123",
  "mlflow_run_id": "run_abcdef",
  "eval_comparison": {
    "base_faithfulness": 0.84,
    "fine_tuned_faithfulness": 0.91,
    "base_answer_relevance": 0.82,
    "fine_tuned_answer_relevance": 0.89,
    "promoted_to_router": true
  },
  "started_at": "2026-07-02T10:30:05Z",
  "finished_at": "2026-07-02T11:45:00Z"
}
```

**Possible `status` values:** `queued`, `running`, `succeeded`, `failed`, `cancelled`.

**Errors:** `404 not_found` (unknown `job_id`).

---

## `GET /health`

Liveness/readiness check.

**Auth:** none
**Rate limit:** none (excluded from rate limiting)

**Response `200 OK`:**
```json
{
  "status": "ok",
  "checks": {
    "postgres": "ok",
    "pgvector": "ok",
    "llm_provider": "ok",
    "mlflow": "ok"
  },
  "version": "1.0.0"
}
```

**Response `503 Service Unavailable`** if any critical dependency check fails; body lists which
`checks` entry is `"down"`.

---

## `GET /metrics`

Prometheus-format metrics endpoint (request rates, latencies, token usage, queue depths).

**Auth:** internal network only (no bearer token; restricted at network/ingress layer)
**Rate limit:** none (scrape endpoint)

**Response `200 OK`:** `Content-Type: text/plain; version=0.0.4` — standard Prometheus exposition
format, e.g.:
```
# HELP neuroflow_query_latency_ms Query latency in milliseconds
# TYPE neuroflow_query_latency_ms histogram
neuroflow_query_latency_ms_bucket{le="100"} 120
neuroflow_query_latency_ms_bucket{le="500"} 980
...
```
