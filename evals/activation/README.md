# Natural Activation Evaluation

This maintainer-only harness measures routing separately from engineering behavior. It never enters the distributable `engineering-core/` tree and never installs a router or hook.

Datasets are intentionally split into positive, negative, and ambiguous prompts. Smoke contains 8 positives, 4 negatives, and 2 ambiguous cases; full contains all cases. Ambiguous results are reported but excluded from binary confusion metrics.

Evidence tiers:

- Tier A: a structured runtime tool trace explicitly loads `engineering-core`;
- Tier B: a valid `### Execution Summary` names `Policy: engineering-core`;
- Tier C: several distinctive policy behaviors are visible, without a structured activation signal.

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
