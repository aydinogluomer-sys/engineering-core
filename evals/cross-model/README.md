# Cross-Model Reliability Harness

This maintainer-only layer measures model-specific routing and normalizes report provenance. It is not part of the installed `engineering-core` runtime package.

The registry defines stable CLI aliases and reliability roles. Reports distinguish the requested alias from the observed served model. When Claude Code emits no served-model field, the harness records `effective_model: UNOBSERVED` and `fallback_detected: unknown`; it never infers either value.

Run the bounded mode-selection corpus for one model at a time:

```bash
python evals/cross-model/run_mode_selection_eval.py --model sonnet --total-budget 1.50
```

Use `--case M-01`, `--repetitions 3`, and a lower `--total-budget` for targeted probes. Automatic retries are fixed at zero. A total-budget reservation overflow becomes `BLOCKED: budget`; individual results remain visible.

Each report retains per-case decisions and emits overall/per-mode accuracy, Fast-Exit false-positive rate, Team over-trigger and under-trigger rates, and abort accuracy. Tier A is recorded only when a structured `Skill(engineering-core)` event is present. Each run uses a nested disposable Git repository so parent-worktree state cannot contaminate routing evidence.

Other suites retain their purpose-built runners:

```bash
python evals/activation/run_activation_eval.py --mode natural --dataset holdout --model opus
python evals/run_l4_eval.py --model fable
python evals/formal-spec-team/run_team_eval.py --model sonnet
```

Run static tests with:

```bash
python evals/cross-model/test_cross_model_matrix.py
```

Raw reports under `reports/` are ignored because they may contain model output and local paths. Inspect and redact before publishing evidence summaries.
