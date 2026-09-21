# Natural Activation Evaluation

This maintainer-only harness measures routing separately from engineering behavior. It never enters the distributable `engineering-core/` tree and never installs a router or hook.

The tuning datasets are split into positive, negative, and ambiguous prompts. Smoke contains 8 positives, 4 negatives, and 2 ambiguous cases; full contains all tuning cases. The separately versioned holdout contains 32 positives, 22 negatives, and 12 ambiguous cases and was frozen before scoring. Ambiguous results are always excluded from binary confusion metrics.

Evidence tiers:

- Tier A: a structured runtime tool trace explicitly loads `engineering-core`; this is the only tier used for confusion metrics.
- Tier B: a valid `### Execution Summary` names `Policy: engineering-core`; reported separately.
- Tier C: several distinctive policy behaviors are visible, without a structured activation signal; never counted as activation.

Skill availability in a Claude init event is not activation. Explicit invocation and natural selection run as separate modes.

Run static tests first:

```bash
python evals/activation/test_activation_eval.py
```

Run bounded smoke evaluations before any full set:

```bash
python evals/activation/run_activation_eval.py --mode explicit --profile smoke --limit 2 --model haiku --per-case-budget 0.20 --total-budget 0.40
python evals/activation/run_activation_eval.py --mode natural --profile smoke --description current --model haiku --per-case-budget 0.20 --total-budget 2.80
```

Candidate descriptions can be compared with `--description baseline|candidate1|candidate2|current`. Each case uses a disposable Git repository and process. Reports under `evals/activation/reports/` can contain model text and local paths, are ignored by Git, and must be inspected before sharing.

Once the description is frozen, run the sealed holdout without candidate comparison:

```bash
python evals/activation/run_activation_eval.py --dataset holdout --mode natural --description current --model sonnet --per-case-budget 0.30 --total-budget 19.80
python evals/activation/run_activation_eval.py --dataset holdout --mode natural --description current --model haiku --per-case-budget 0.20 --total-budget 13.20
```

Use `--repetitions 2` or `3` only when the total budget permits. Every repetition gets a new disposable repository and process. Do not revise the description from holdout outcomes; retain failures as evidence for a future versioned cycle.

For a bounded stability probe, combine repeatable `--case ID` filters with `--repetitions 3`; filtering occurs before repetition expansion.

The v3 report adds per-prompt activation rates, explicit positive/negative/ambiguous and blocked/timeout counts, role-aware gates, and requested/effective-model provenance. Repetition activation rate is Tier-A runs divided by all runs, including blocked attempts. Tier A alone controls confirmed confusion matrices. Missing runtime model identity is `UNOBSERVED`; it is never inferred from the requested alias.

Formal-spec and long-horizon closure uses a separate versioned corpus so the frozen holdout is not edited or reused as a tuning set:

```bash
python evals/activation/run_activation_eval.py --dataset targeted --mode natural --model sonnet --repetitions 3 --per-case-budget 0.30 --total-budget 13.50
```

Run Opus and Fable separately with their own explicit total budgets. A budget overflow remains `BLOCKED: budget` and is excluded from the confusion matrix; it is not converted into TP or FN.
