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
<!-- policy-id: blocking-verification -->

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

For Formal Spec Team Mode, maintain the full requirement coverage matrix and scan both directions before closure: an executable requirement without work/evidence is an orphan requirement; a meaningful diff without requirement/correctness justification is an orphan change. Moderate/High/Critical phase closure requires implementation plus independent evidence. A fresh release audit must reconcile all phases, locks, findings, deferrals, and cross-cutting gates before `RELEASE_VERIFIED`.

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
<!-- policy-id: completion-output -->

Report separately:

### Implemented
What changed.

### Verified
Commands/observations executed after the final relevant edit.

### Not verified / limitations
Anything inferred, blocked, unavailable, flaky, or not run.

Completion-state rules:

- a relevant required check failure -> `NOT_VERIFIED` or `BLOCKED`;
- a required unavailable check without equivalent evidence -> `NOT_VERIFIED` or `BLOCKED`;
- an optional unavailable check -> explicit limitation; completion may remain possible;
- a proven unrelated/pre-existing failure -> report causality and impact; scoped completion may remain possible only if required evidence is intact.

Never use “complete but not verified.” A completion report is a claim, not the evidence itself; record commands and observations separately, and let independent evaluators compare those claims with actual diff/test evidence. Never claim:

- all tests pass;
- fully secure;
- production ready;
- complete;

without evidence supporting that exact claim.

### Execution Summary contract

Every substantive `engineering-core` execution ends at a level-three heading named `Execution Summary`. Use Markdown fields, not custom JSON/YAML:

- `Policy: engineering-core`
- `Risk: Low|Moderate|High|Critical`
- `Status: NO_CHANGE|IMPLEMENTED|VERIFIED|NOT_VERIFIED|BLOCKED`
- `Changed:` concise outcome or `None`
- `Verified:` commands/observations actually executed, or `Not run`
- `Limitations:` known gaps, optional unavailable evidence, or `None`

For Low work, these fields are normally enough. For Moderate, High, or Critical work, add only relevant sections such as Files Changed, Negative Paths, Unverified, Blockers, or Security. Do not emit empty boilerplate. `VERIFIED` means all required scoped evidence passed after the final relevant edit and no blocker remains. `IMPLEMENTED` means the change exists but required verification is incomplete. `NO_CHANGE` means no repository mutation was needed or authorized. `NOT_VERIFIED` means required evidence failed or is unavailable without equivalent proof. `BLOCKED` means progress cannot safely continue within current authority/capability. A required failure or nonempty blocker cannot coexist with `VERIFIED`.

Before sending, confirm that all six required fields are present; use `Limitations: None` rather than omitting the field. Use only the controlled risk labels—never substitutes such as “Medium.” Do not describe a command, test, stage, commit, release, or deployment as observed unless it actually occurred.

## Frontend / browser verification
<!-- policy-id: frontend-verification -->

Use this profile only when the changed behavior depends on rendering, browser APIs, interaction, responsive layout, accessibility, or client/server integration.

- Prefer the repository's existing browser/UI tooling; do not auto-install a browser, driver, plugin, or service.
- Start with component/unit/static evidence, then use browser evidence when those layers cannot prove the behavior or risk warrants it.
- Verify task-relevant states: initial/loading, empty, error, disabled/unauthorized, narrow viewport, keyboard/focus, and recovery only as applicable.
- Inspect console/network behavior and visual output when relevant; a screenshot alone does not prove interaction or accessibility.
- If browser tooling is unavailable, use the strongest native fallback and classify the missing evidence as optional limitation or required blocker according to the contract.

A one-line styling or copy fix can remain Low risk with a focused render/static check and diff review.

## Dependency changes
<!-- policy-id: dependency-change -->

Before adding, removing, or upgrading a dependency:

- prove necessity and check for an existing repository/platform primitive;
- verify supported version, runtime/platform compatibility, lockfile effect, transitive impact, and build/bundle impact;
- consider provenance, maintenance, known security posture, license, and supply-chain exposure proportionately;
- identify config, migration, rollback/roll-forward, and deployment implications;
- read relevant upgrade notes and breaking changes for upgrades;
- keep manifest and lockfile changes intentional and review their diff.

Do not install tooling merely to improve investigation. A dependency change expands scope and must be authorized by the requested implementation or correctness need.

## Performance work
<!-- policy-id: performance-work -->

Use the sequence:

`BASELINE -> HYPOTHESIS -> CHANGE -> MEASURE -> COMPARE`

Define the metric, workload, environment, and correctness invariant before optimizing. Measure baseline and candidate under materially equivalent conditions, account for warmup/noise/variance, and retain raw results when practical. Reject regressions in correctness or important secondary metrics. Report only observed deltas; do not call speculative complexity reduction a measured performance improvement.
