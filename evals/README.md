# L4 Live Evaluation

This harness tests observed Claude Code behavior, not just policy text. Every case runs in its own disposable Git repository with a project-scoped copy of `engineering-core`. Fixtures contain no secrets and require no external service.

Explicit activation (`/engineering-core`) and natural activation are separate measurements. The six core fixtures currently use explicit activation so a policy-behavior failure is not confused with model routing. Natural-activation cases can be added without changing the scorer.

Run a cheap case first:

```bash
python evals/run_l4_eval.py --case small --model haiku --per-case-budget 0.35 --total-budget 0.35
```

Run all core cases:

```bash
python evals/run_l4_eval.py --model haiku --per-case-budget 0.35 --total-budget 2.10
```

The harness records JSONL tool/event output, process exit/stderr, timeout/cost, Git status/diff, independent tests, hashes, and machine assertions under `evals/reports/`. A zero exit code is never sufficient for `PASS`. Reports may contain model output and local paths; inspect before sharing. Runtime reports are ignored by Git.

Statuses are `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`. Failure classes are `activation`, `model`, `budget`, `timeout`, `fixture`, `CLI`, `permission`, `policy`, `scoring`, or `unknown`. Retries default to zero; change strategy before retrying.
