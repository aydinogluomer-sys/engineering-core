# Worked Example: Large Specification Execution

## Request

“Implement this 2,000-line `implementation.md` hardening plan.”

## Classification

- Task: formal specification / multi-phase implementation.
- Risk: determined per work unit; overall process may contain High/Critical phases.
- Horizon: long-running.

## 1. Parse the contract

Extract:

- authoritative requirements;
- acceptance criteria;
- dependencies;
- explicit deferrals;
- Decision Locks/constraints;
- validation gates.

Do not treat background prose as a requirement unless the spec does.

## 2. Build work units

Example ledger:

| Work unit | Depends on | Status | Required evidence |
|---|---|---|---|
| A: request identity invariant | none | VERIFIED | targeted tests + diff |
| B: durable idempotency | A | IN_PROGRESS | replay/duplicate/failure tests |
| C: privilege hardening | A | NOT_STARTED | role/negative-path tests |
| D: release audit | B, C | NOT_STARTED | cross-cutting suite |

Use statuses:

`NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`, `VERIFIED`, `BLOCKED`, `DEFERRED`, `NOT_APPLICABLE`.

## 3. Execute in dependency order

For each unit:

1. inspect current code/state;
2. confirm prerequisite evidence;
3. implement the bounded change;
4. run the unit's verification;
5. update status;
6. preserve unresolved findings.

Do not mark `IMPLEMENTED` as `VERIFIED`.

## 4. Phase closure

Suppose Phase B passes all scoped invariants.

Record:

`Phase B = VERIFIED`

Do not translate that into:

`Release = VERIFIED`

A closed phase is not reopened for speculative edge-case hunting without new evidence.

## 5. New evidence can reopen

If the final release audit discovers a cross-cutting failure that invalidates a closed phase's assumptions, reopen the affected phase with the new evidence and reverify it.

## 6. Final cross-cutting audit

Only after dependencies/phases are complete, evaluate:

- requirement coverage;
- shared interfaces;
- security boundaries;
- migrations/data state;
- replay/concurrency behavior;
- integration tests;
- release gates;
- unresolved blockers.

## 7. Long-horizon state

Persist only compact continuation-critical state in an approved task system/file:

- current phase/work unit;
- verified invariants;
- modified files;
- current evidence;
- blockers;
- next action.

On resume, verify repository state rather than trusting stale notes.

## Completion

A correct report distinguishes:

- phases implemented;
- phases verified;
- release audit status;
- blocked/deferred items;
- checks not run.
