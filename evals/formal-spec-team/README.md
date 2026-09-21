# Formal Spec Team Mode L4 Evaluation

This maintainer-only harness evaluates mode selection and orchestration in disposable Git repositories. It is not installed with the runtime skill and never targets a production repository.

## Machine artifact contract

Scenarios request JSON evidence so PASS does not depend on prose:

- `section-inventory.json`: `{"sections":[{"id":"S-001","classification":"requirement","executable":true}]}`
- `coverage.json`: `{"requirements":{"REQ-001":{"work_unit":"WORK-001","status":"VERIFIED","evidence":["..."]}},"decision_locks":{"LOCK-001":"LOCKED"},"deferrals":["..."]}`
- `team-state.json`: `{"phases":{"A":"VERIFIED"},"requirements":{"REQ-001":"VERIFIED"},"transitions":["..."]}`
- `finding-ledger.json`: `{"findings":[{"id":"FIND-001","status":"VERIFIED_FIXED","evidence":["..."]}]}`
- `qa-report.json`: `{"independent":true,"acceptance_covered":true,"negative_paths":true,"implementation_key":true,"independent_key":true}`
- `release-audit.json`: `{"fresh":true,"caught_seeded_defect":true,"release_status":"RELEASE_VERIFIED","evidence":["..."]}`
- requirement-change/resume scenario evidence uses the boolean keys named in its scenario assertions.

Artifacts are claims until the scorer reconciles them with independent tests, Git status/diff/index, protected hashes, expected IDs, original spec, and process count.

Run unit/self-tests first:

```bash
python evals/formal-spec-team/test_team_eval.py
```

Then run one cheap case before larger cases:

```bash
python evals/formal-spec-team/run_team_eval.py --case two-key-closure --model haiku
python evals/formal-spec-team/run_team_eval.py --case large-spec --model sonnet
```

Independent QA and fresh release-auditor roles run in separate Claude processes where the scenario requires them. The scorer also requires an artifact to record selection of `Formal Spec Team Mode`; prose alone is insufficient.

Every scenario uses its own configured budget and timeout unless stricter CLI caps are supplied. `--total-budget` reserves the whole run before each scenario, `--repetitions` creates independent disposable runs, and `--retries` is fixed at zero. An unobserved process cost consumes its reservation instead of failing open. Budget overflow is retained as `BLOCKED: budget`. Raw redacted reports are written under the ignored `reports/` directory.

Reports use the shared v3 provenance contract. They distinguish the requested alias from the effective model observed in runtime events; missing or inconsistent evidence becomes `UNOBSERVED` with fallback ambiguity. Repetition summaries retain PASS, FAIL, BLOCKED, cost variance, and failure classes per scenario.

The 9.8 matrix requires all five scenarios to pass independently on Sonnet, Opus, and Fable. Historical Sonnet PASS evidence is retained; Opus/Fable remain `NOT_RUN` until an explicitly budgeted live evaluation is performed.
