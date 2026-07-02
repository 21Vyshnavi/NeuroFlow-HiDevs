# ADR-003: Evaluation Framework — LLM-as-judge over human annotation only

**Status:** Accepted
**Date:** 2026-07-02

## Context

Every generation needs to be scored on faithfulness, answer relevance, context precision, and
context recall, and those scores feed both the rolling quality dashboards and the fine-tuning
data selection filter (`faithfulness > 0.8 AND user_rating >= 4`). This requires evaluation at the
volume of production traffic — potentially thousands of generations per day — which is not
feasible to cover with human annotation alone: human review is accurate but slow, expensive, and
does not scale to full-traffic coverage. Human annotation-only would force sampling, meaning most
generations (and most fine-tuning candidates) would go unscored.

## Decision

Use **automated LLM-as-judge evaluation** as the primary, full-coverage scoring mechanism for all
four metrics, with human annotation used as a calibration and spot-check layer rather than the
primary scoring path.

- Every generation is scored by a judge LLM, separate from the generation model (to reduce
  self-preference bias), immediately and asynchronously after generation.
- A sampled subset of generations (e.g. 2-5% stratified by score bucket, plus 100% of low-score
  outliers) is periodically routed to human review to validate that judge scores correlate with
  human judgment.
- User feedback (`user_rating` 1-5) is collected directly from end users as a separate, real-world
  signal that combines with the LLM-judge's `faithfulness` score to gate fine-tuning data
  selection — this is a deliberate second signal, not a replacement for human annotation.

## Consequences

**Positive:**
- Full-coverage scoring: every generation, not a sample, gets faithfulness/relevance/precision/
  recall scores — necessary for the fine-tuning pipeline to have a large enough qualifying pool.
- Fast feedback loop: scores are available minutes after generation, enabling near-real-time
  quality dashboards instead of a batch human-review cadence.
- Meaningfully cheaper per-generation than human review at this volume.

**Negative — known failure modes and detection:**

| Failure mode | Description | Detection |
|---|---|---|
| **Self-preference / stylistic bias** | Judge LLM rates fluent, confident-sounding answers higher regardless of actual grounding. | Human calibration sample compares judge scores to human scores on the same generations; systematic gaps trigger a prompt/model review. |
| **Judge hallucination** | Judge itself fabricates a rationale not grounded in the actual context/answer. | `judge_rationale` is stored per evaluation specifically so it's auditable; spot-checked during calibration review. |
| **Metric correlation collapse** | Judge scores all four metrics near-identically regardless of actual differences (judge isn't actually discriminating). | Monitor score variance/distribution per metric in `evaluation_aggregates`; near-zero variance across a large sample is a red flag. |
| **Prompt sensitivity / drift** | Judge model provider updates the underlying model, silently shifting score calibration over time. | Judge model version is pinned and logged (`judge_model` column); score distributions are tracked over time to catch step-changes after any judge model change. |
| **Gaming via fine-tuning feedback loop** | Since fine-tuning selects on `faithfulness > 0.8`, a miscalibrated judge could reinforce its own blind spots into future models. | Held-out benchmark evaluation for fine-tuned models (see architecture.md §5) is deliberately a separate, fixed benchmark set — not just "more judge scores" — to catch this loop before promotion. |

## Revisit trigger

If the human-calibration sample shows judge-vs-human agreement dropping below an acceptable
threshold (e.g. Cohen's kappa < 0.6) on any metric for two consecutive review cycles, pause
fine-tuning data selection on that metric and escalate to a prompt/model revision before resuming.
