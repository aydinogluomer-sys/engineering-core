# Verification and Review

Read this reference for moderate, high, or critical-risk work; removals; review; testing; release preparation; and completion claims.

## 1. Verification scales with risk

Start focused, then broaden only when blast radius justifies it.

Typical order:

`syntax/static -> targeted unit -> module -> type/lint -> integration -> E2E -> broader regression`

Do not run the most expensive suite first merely because it exists.

### Low

- narrow meaningful check;
- final diff review.

### Moderate

- targeted tests;
- relevant integration/static checks;
- affected-module regression;
- diff review.

### High

Also require, as applicable:

- explicit invariants;
- negative/failure paths;
- compatibility/concurrency/replay checks;
- security or specialist review;
- broader regression;
- release gates.

### Critical

Critical work receives at least all applicable High protections, plus:

- exact action/target authorization;
- consequence/reversibility review;
- production/external mutation gates;
- explicit evidence before the consequential action.

## 2. Negative-path testing

Select only relevant cases.

Consider:

- unauthorized caller;
- invalid input;
- duplicate/replay;
- timeout;
- provider failure;
- partial failure;
- process death;
- retry;
- stale state;
- concurrency;
- wrong tenant;
- missing permission;
- malformed payload;
- expired token;
- ordering inversion.

Do not create meaningless combinatorial explosion.

## 3. Stale evidence rule

A test pass is evidence only for the code/state it actually tested.

After a relevant final edit, rerun affected checks.

A state record saying “tests passed” from before later edits is historical evidence, not current evidence.

## 4. Diff-first review

Before completion, inspect final status and diff.

Ask:

- Is every change intentional?
- Is anything unrelated included?
- Are generated/untracked files expected?
- Are there accidental formatting changes?
- Did a shortcut leak in?
- Are debug logs or temporary artifacts left?
- Did API/schema/config behavior change unintentionally?
- Are secrets or credentials present?
- Are tests checking the intended contract?

A green test run does not replace diff review.

## 5. Spec-to-code compliance

When a formal specification exists, maintain:

`requirement -> implementation location -> verification evidence -> status`

For each requirement classify:

- implemented;
- verified;
- blocked;
- deferred;
- not applicable.

Do not silently omit requirements.

Phase verification does not imply release verification. See `operating-model.md`.

## 6. Removal/completeness audit

Deleting a primary file is not enough.

Check relevant:

- imports;
- exports;
- routes;
- registries;
- feature flags;
- configuration;
- environment variables;
- database/IaC objects;
- tests;
- docs;
- build/CI;
- dependencies;
- assets;
- generated references;
- compatibility paths.

Completion criterion:

“No unintended live references remain.”

Use Cartographer-style removal ledgers when available, otherwise native searches.

## 7. Independent/fresh review

For Moderate, High, and Critical work, use fresh review when available and proportionate.

The reviewer should receive:

- user request / specification;
- relevant repository instructions;
- actual diff;
- relevant surrounding code/tests;
- validation evidence.

Do not prime the reviewer with the implementer's conclusion as the source of truth.

Review:

- requirement coverage;
- logic defects;
- side effects;
- security implications;
- missing edge cases;
- test adequacy;
- architecture consistency;
- unnecessary complexity.

If review finds a defect:

`IMPLEMENT -> VERIFY -> REVIEW`

## 8. Release gate

For explicit merge/release/deploy/hardening work, evaluate:

- code status;
- tests/build;
- migration readiness;
- config/env requirements;
- secrets;
- monitoring/operability implications;
- backward compatibility;
- rollback/roll-forward;
- unresolved issues;
- exact authorization for consequential actions.

“Mergeable” does not mean “production ready.”

“Locally verified” does not mean “deployed.”

## 9. Evidence-based completion

Report separately:

### Implemented
What changed.

### Verified
Commands/observations executed after the final relevant edit.

### Not verified / limitations
Anything inferred, blocked, unavailable, flaky, or not run.

Never claim:

- all tests pass;
- fully secure;
- production ready;
- complete;

without evidence supporting that exact claim.
