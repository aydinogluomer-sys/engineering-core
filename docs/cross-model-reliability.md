# Cross-Model Reliability

This report separates four questions that cannot be collapsed into one score:

`activation != mode selection != policy execution != long-horizon orchestration`

## Current evidence matrix

| Model | Role | Natural activation | Mode selection | Core L4 | Team L4 |
|---|---|---|---|---|---|
| Haiku | degradation benchmark | MEASURED / below gate | NOT_RUN | PASS (six historical scenarios) | optional / not claimed |
| Sonnet | workhorse baseline | PASS aggregate gate; formal-spec and long-horizon below category gate | NOT_RUN | NOT_RUN | PASS (five historical scenarios) |
| Opus | high-capability baseline | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Fable | long-horizon baseline | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |

The 9.8 cross-model gate is `NOT_VERIFIED`. Static harness capability is not live behavioral evidence. Opus/Fable are not substituted with other models, and Haiku is not averaged with stronger models.

## Divergence retained from current evidence

| Model | Strengths observed | Weaknesses / unknowns | Tendency evidence | Cost / timeout profile | Completion format |
|---|---|---|---|---|---|
| Haiku | Historical six-case explicit core suite passed; debugging activation was strongest | Natural activation recall 0.1724; most consequential categories were weak; three positive cases blocked | Mode, delegation, investigation, and closure tendencies are NOT_RUN | Historical holdout `$3.555201`; one database timeout | Core fixture summaries passed after calibration; no cross-model rate claimed |
| Sonnet | Natural precision 1.0 / recall 0.8438; full five-case Team suite passed | Formal-spec 0/2 and long-horizon 0/1 natural activation; core suite not durably run | Team execution is evidenced; over/under-delegation and mode-selection corpus are NOT_RUN | Historical holdout `$4.335969`; Team final PASS cells total `$1.946492` | Team artifacts passed machine scoring; no general format rate claimed |
| Opus | None yet | All required live cells NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Fable | None yet | All required live cells NOT_RUN; served-model identity must not be inferred from the requested alias | NOT_RUN | NOT_RUN | NOT_RUN |

## Provenance semantics

Every v3 report records `requested_model`, `effective_model`, `effective_model_observed`, `fallback_detected`, and `fallback_reason`. A runtime model field is recorded as observed evidence. Missing or inconsistent fields yield `effective_model: UNOBSERVED` and `fallback_detected: unknown`. Requested Fable is never reported as effectively served Fable without runtime evidence.

## Budget and repeatability boundary

Live runners expose model/scenario filters, per-case or per-process budget, total budget, timeout, repetitions, and zero automatic retries. The full v3 matrix is intentionally not ordinary CI. It requires an explicit bounded spend decision; failures and blocked runs are retained rather than retried until green.

L5 longitudinal reliability remains unclaimed.
