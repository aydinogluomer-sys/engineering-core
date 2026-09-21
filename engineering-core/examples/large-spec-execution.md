# Worked Example: Formal Spec Team Mode

## Request and mode

“Execute this multi-phase implementation contract, preserve its Decision Locks, verify each phase independently, and complete the release audit.”

The contract has several dependent phases, High-risk authorization work, explicit deferrals, and likely session boundaries. Choose Formal Spec Team Mode and keep the original `implementation.md` authoritative.

### Counterexample: a formal file that stays Standard

A five-item contract describing one tightly coupled parser correction, one module, one focused test, and no specialist, phase/release, or resume need stays Standard Engineering Mode. The formal document is authority, not automatic Team eligibility. If the parser change is consequential it may still be Moderate/High and therefore not Fast-Exit, but one bounded writer and proportional review are enough.

## 1. Compile the specification

Create a compact Section Inventory without copying the full spec:

| Section | Class | Executable |
|---|---|---|
| S-001 | requirements / Phase A | yes |
| S-002 | Decision Locks | attached constraint |
| S-003 | Phase B acceptance | yes |
| S-004 | deferred provider | no/current deferral |
| S-005 | release gate | yes |

Extract `REQ-001` onward, acceptance criteria, dependencies, risk, intended evidence, and locks. Reconcile every section and acceptance criterion. An executable item without a work unit blocks planning; a work unit without requirement/correctness justification is scope drift.

## 2. Build dependency-aware work units

Example graph:

```text
WORK-001 model contract (REQ-001, REQ-002)
  -> WORK-002 API consumer (REQ-003)
  -> WORK-003 authorization boundary (REQ-004, High)
WORK-002 + WORK-003
  -> WORK-004 UI integration (REQ-005)
all work units
  -> release audit (REQ-006)
```

Each unit names one writer, allowed files, forbidden changes, artifacts, checks, stop conditions, specialist need, and evidence. Parallelize only independent non-overlapping ownership; do not spawn agents to make the topology look busy.

## 3. Execute with independent QA

The builder implements `WORK-003` and records current targeted tests. Independent QA receives the original authorization requirement, acceptance, lock, actual diff, and tests—not “the builder says it passes.” QA discovers that same-tenant success is covered but cross-tenant denial is missing.

Record:

| Finding | Link | State | Evidence |
|---|---|---|---|
| FIND-001 | REQ-004 / WORK-003 | OPEN | no forbidden-path test |

The phase is `IMPLEMENTED`, not `VERIFIED`. After the writer adds the correct negative test and QA independently observes it pass, mark `FIND-001` `VERIFIED_FIXED`.

## 4. Two-Key closure

Close the Moderate/High phase only when both are current:

- implementation key: intended diff/artifacts and targeted checks;
- independent key: QA acceptance mapping, negative paths, and required security specialist evidence.

Then mark `PHASE_VERIFIED`. This does not imply release verification.

## 5. Requirement change and selective STALE

After Phase A is verified, the user changes retry semantics in `REQ-005` and its release criterion. Preserve unaffected Phase A. Mark `REQ-005`, its work unit, downstream integration, and affected release evidence `STALE`; update acceptance and reverify that path. Do not restart unrelated verified work or keep obsolete green checks.

## 6. Cross-session resume

Before a session boundary, use the single [canonical Compact State schema](../references/collaboration-state.md#6-canonical-compact-state); do not reproduce a second field list here. A fresh session follows that reference's resume protocol and does not trust a note saying “tests passed.”

## 7. Fresh release audit

Give a fresh auditor the original spec, repository instructions, base-to-HEAD diff, coverage matrix, locks, phase evidence, Finding Ledger, deferrals, and release gates. Do not prime it with a success conclusion.

The auditor scans source sections, orphan requirements/diffs, locks, specialists, Two-Key closures, findings, migrations, integration invariants, and stale evidence. If a cross-module API mismatch remains, verdict is `RELEASE_NOT_VERIFIED` or `RELEASE_BLOCKED` even though individual phases are green. After correction and current cross-cutting evidence, it may become `RELEASE_VERIFIED`.

## Completion

Use the universal `### Execution Summary` with relevant Team Mode fields: Policy, Mode, Risk, Status, Phases, Requirements, Verification, Findings, Deferred, Limitations, and Release Status. Keep `PHASE_VERIFIED != RELEASE_VERIFIED` explicit.
