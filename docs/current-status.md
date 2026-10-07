# Current validation status

Canonical status owner. Updated 2026-10-06 against the final pre-commit candidate based on `6940e92aa1164c6b857d4bf7de9fbc622806ec17`. The evidence bundle records the final validated candidate manifest; publication and remote controls remain separate claims.

## Claim matrix

| Claim | Status | Current evidence / limitation |
|---|---|---|
| Runtime skill structure and policy lint | PASS | `validate_skill.py`; 28 validator mutation tests |
| Completion/report/event strictness | PASS | schema v3, completion, common harness, cross-model adversarial tests |
| Trusted oracle and scope integrity | PASS | evaluator-owned oracle and Git/scope negative controls |
| Evidence freshness and continuation state | PASS | relevant/unrelated staleness, resume identity, CAS, recovery, graph, ownership tests |
| Team stage provenance and Two-Key scorer | PASS | evaluator-owned stage records, QA/auditor authorship chain, oracle trajectory, role/stage/artifact-bound finding closure, semantic coverage validation; final targeted independent re-audit PASS |
| Deterministic failure-resistance fixtures | PASS | source-risk transition, coordination, specialist, and injection baseline/fixed tests |
| Installer behavior | PASS | fresh, no-op, equal-content provenance refresh, drift refusal, explicit replace, failure-safe staging, backup/rollback, anti-nesting tests |
| CI/repository structure | PASS | structural workflow parser, mutations, SHA pins, repository validator |
| TypeScript integration fixture | BLOCKED | Node exists; a real `tsc` compiler is not installed, so no typecheck PASS is claimed |
| PostgreSQL/RLS integration fixture | BLOCKED | local `psql`/disposable PostgreSQL capability unavailable |
| Browser interaction fixture | BLOCKED | supported local browser executable not detected |
| GitHub branch protection | NOT_APPLIED | profile prepared in `docs/governance.md`; no settings mutation authorized |
| Tag / GitHub release / publication | NOT_AUTHORIZED | prerelease metadata exists locally only |
| Live Haiku/Sonnet/Opus/Fable reliability matrix | NOT_RUN | concrete manifest is frozen as a non-executable proposal; no exact spend authorization/evidence was granted |
| Seven-day longitudinal field reliability | NOT_RUN | protocol prepared; seven elapsed days and independent field audit not performed |

## Local validation commands

The evidence bundle records exit codes and redacted output tails for:

```text
python engineering-core/scripts/validate_skill.py engineering-core
python engineering-core/scripts/test_validate_skill.py
python -m unittest discover -s evals -p test_*.py
python -m unittest discover -s evals/activation -p test_*.py
python -m unittest discover -s evals/formal-spec-team -p test_*.py
python -m unittest discover -s evals/cross-model -p test_*.py
python -m unittest discover -s evals/failure-resistance -p test_*.py
python scripts/test_install.py
python scripts/test_validate_repository.py
python scripts/validate_repository.py .
python -m compileall -q engineering-core scripts evals
```

Passing these commands demonstrates deterministic local behavior of the package and harness. It does not demonstrate served-model identity, paid live-model reliability, production database/browser behavior, applied GitHub controls, or longitudinal effectiveness.

## Evidence boundaries

- Model-authored artifacts are claims until reconciled with evaluator-owned records and protected checks.
- A candidate-visible test is developer feedback, not the trusted acceptance oracle.
- `evaluation_completed` and `quality_gate_passed` are separate fields and exit semantics.
- Unknown post-invocation cost consumes the reserved budget.
- Historical reports remain historical; schema adapters do not grant current quality-gate status.
- Deterministic simulations and live-agent measurements are never merged.
- Hashes demonstrate byte integrity, not correctness or reviewer independence.

See the sanitized local bundle in [`../evidence/current/`](../evidence/current/) after generation and its `SHA256SUMS.json` manifest.
