# L4 Live Evaluation

This harness tests observed Claude Code behavior, not just policy text. Every case runs in its own disposable Git repository with a project-scoped copy of `engineering-core`. Fixtures contain no secrets and require no external service.

Explicit activation (`/engineering-core`) and natural activation are separate measurements. The six core behavior fixtures use explicit activation so policy behavior is not confused with model routing. Natural selection is measured by the separate positive/negative/ambiguous harness in [`activation/README.md`](activation/README.md).

Formal Spec Team Mode uses a distinct five-scenario harness because its evidence contract includes requirement compilation, independent QA, Two-Key closure, cross-session state, selective invalidation, and fresh release audit. See [`formal-spec-team/README.md`](formal-spec-team/README.md).

Cross-model provenance, the four-role registry, report schema, and bounded mode-selection corpus live in [`cross-model/README.md`](cross-model/README.md). These tools keep activation, mode selection, core execution, and Team reliability separate and never average model results.

Run a cheap case first:

```bash
python evals/run_l4_eval.py --case small --model haiku --per-case-budget 0.35 --total-budget 0.35
```

Run all core cases:

```bash
python evals/run_l4_eval.py --model haiku --per-case-budget 0.35 --total-budget 2.10
```

The harness records JSONL tool/event output, process exit/stderr, timeout/cost, Git status/diff, independent tests, hashes, parsed completion claims, and machine assertions under `evals/reports/`. A zero exit code or a model-written `VERIFIED` claim is never sufficient for `PASS`; the scorer compares the completion contract with independent fixture evidence. Reports may contain model output and local paths; inspect before sharing. Runtime reports are ignored by Git.

Standardized report statuses are `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`. The shared failure taxonomy distinguishes activation, mode selection, policy, specification, QA, closure, stale state, release audit, fallback/provenance, model capability, timeout, budget, permission, CLI, fixture, scorer, environment, and unknown failures. Retries are fixed at zero; change strategy or fixture before rerunning.

Every standardized report records requested and effective-model provenance. `UNOBSERVED` is an explicit state, not a model guess. Live multi-model runs are manual and budget-controlled; push CI runs unit/schema/scorer checks only.
