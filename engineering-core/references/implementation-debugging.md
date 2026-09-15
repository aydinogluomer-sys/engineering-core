# Implementation and Debugging

Read this reference for implementation tactics, bug fixing, failing tests, uncertain causes, repeated failures, and failure classification.

## 1. Minimum-correct implementation

Optimize for the smallest change that completely satisfies the requirement and repository invariants.

This does not mean minimum line count.

Prefer:

- established local patterns;
- existing abstractions that actually fit;
- direct behavior over speculative extension points;
- clear contracts over defensive noise.

Avoid:

- opportunistic refactors;
- unrelated cleanup;
- new dependencies for trivial helpers;
- speculative configurability;
- broad formatting churn;
- replacing working frameworks.

Validate aggressively at trust boundaries. Trust well-defined internal invariants where appropriate.

## 2. Never test-cheat

Tests verify behavior; they are not targets to game.

Never:

- hardcode production behavior to fixtures;
- detect test environments to bypass logic;
- weaken assertions simply to turn CI green;
- refresh snapshots without checking behavior;
- suppress errors instead of fixing them;
- mock away the behavior under test;
- alter tests to match a known-wrong implementation.

If a test appears wrong, investigate the intended contract and supporting evidence.

## 3. Bug-fix protocol

Use:

`REPRODUCE -> LOCALIZE -> HYPOTHESIZE -> DISCRIMINATE -> FIX_ROOT_CAUSE -> VERIFY`

### Reproduce

Capture:

- exact failure;
- inputs/state;
- command/environment;
- expected versus observed behavior.

If reproduction is impossible, state what evidence substitutes for it.

### Localize

Trace to the earliest violated invariant, not merely the final symptom.

### Hypothesize

Write a falsifiable explanation.

Bad: “Something in caching is broken.”

Good: “The second request reads stale entry X because invalidation occurs after the consumer read.”

### Discriminate

Run the cheapest experiment that separates the current hypothesis from alternatives.

Change one meaningful variable at a time.

### Fix root cause

Implement the smallest correction at the actual broken boundary.

### Verify

Check:

- original reproduction;
- regression;
- adjacent relevant negative path;
- no new scope drift.

## 4. TDD without dogma

Prefer test-first when it materially reduces regression risk, especially for:

- reproducible bugs;
- deterministic business rules;
- security behavior;
- parsers/state machines;
- edge cases that must not recur.

Do not force test-first for documentation, trivial configuration, purely exploratory visual work, or cases where another verification mechanism is stronger.

The rule is:

“Capture behavior before changing behavior when doing so meaningfully improves confidence.”

## 5. Attempt ledger and loop detection

Track meaningful attempts:

| Attempt | Hypothesis | Experiment | Evidence | Next |
|---|---|---|---|---|

Repeating the same action twice without new evidence triggers a tactic change.

A third equivalent failure requires explicit failure classification before more edits.

When looping:

1. stop;
2. summarize evidence;
3. invalidate stale assumptions;
4. generate distinct hypotheses;
5. inspect a deeper boundary or environment mismatch.

Do not brute-force minor variants indefinitely.

## 6. Failure classification

Before changing production code in response to a failed check, classify the failure:

- implementation defect;
- test-oracle defect;
- environment/tooling;
- dependency/external service;
- permissions/authorization;
- flaky/timing;
- missing prerequisite;
- stale generated artifact;
- migration/state mismatch;
- scope conflict;
- unknown.

Do not “fix” an environment or oracle problem by weakening product behavior without evidence.

## 7. Re-evaluate after diff expansion

After coherent edit groups, inspect the diff.

If implementation spreads beyond the planned surface:

- re-evaluate risk;
- revisit the scope contract;
- identify whether the expansion is required or accidental;
- return to investigation/planning when architecture assumptions proved wrong.
