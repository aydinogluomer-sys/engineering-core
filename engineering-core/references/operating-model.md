# Operating Model

Read this reference for task/risk classification, formal-spec execution, proportional planning, authorization, scope, state transitions, and Definition of Done.

## 1. Task class

Classify the user's request before changing files:

| Class | Default authority |
|---|---|
| Explain / inspect / review | Read-only unless edits are separately requested |
| Diagnose | Find and explain cause; do not silently implement |
| Small correction | Edit only when requested |
| Feature / behavior change | Implement within explicit scope |
| Refactor / removal / migration | Preserve or intentionally change contracts as specified |
| Test / build / release | Follow the requested stage; do not infer deploy authority |
| Security-sensitive / external mutation | Escalate risk and verify exact authority |

Classification determines whether implementation is authorized, not only which workflow to use.

## 2. Risk model
<!-- policy-id: risk-model -->

Use the highest applicable risk dimension. Diff size is not a risk proxy.

1. Start from the apparent task class in section 1.
2. Evaluate only dimensions supported by observed source, configuration, runtime, specification, or user-authority evidence; do not score hypothetical possibilities.
3. Apply every evidenced hard floor below.
4. Classify from the highest remaining applicable dimension and record the evidence that controls the decision.

| Level | Typical properties |
|---|---|
| Low | Localized, reversible, familiar pattern, narrow blast radius |
| Moderate | Multi-file or interacting change with meaningful but contained regression surface |
| High | Shared interfaces, concurrency, persistent data, auth, billing, infrastructure, release gates, hard-to-reverse state |
| Critical | Production mutation, destructive data operation, irreversible external action, credential exposure, uncertain authority |

Assess at least:

- consequence;
- reversibility;
- uncertainty;
- blast radius;
- privilege sensitivity;
- data sensitivity;
- external side effects;
- verification difficulty.

For each dimension, write the observed fact and its consequence rather than assigning a label from intuition. Many low-weight or hypothetical uncertainties do not automatically produce High; concrete blast radius and trust boundaries control. Diff size never lowers a floor.

| Observed surface | Minimum risk |
|---|---|
| Authentication, authorization, RLS, or tenant isolation | High |
| Billing, payment, credit, or money-moving webhook behavior | High |
| Production mutation, irreversible external action, or credential exposure | Critical |
| Schema migration affecting production rows or locking behavior | High |
| Shared public or published API contract | High |

Example: removing one server-side authorization check is still High risk even when it is a one-line deletion. The trusted boundary, not patch size, controls.

Risk may escalate whenever new evidence changes scope or consequence. Downward reclassification requires positive evidence—for example, source and call-site inspection proving that an apparent shared interface is private, local, reversible, and covered by a focused test. Mere absence of discovered problems is not enough.

## 3. Adaptive workflow

Default lifecycle:

`CLASSIFY -> DISCOVER -> INVESTIGATE -> PLAN -> IMPLEMENT -> VERIFY -> REVIEW -> COMPLETE`

Backward transitions are first-class:

- new evidence changes risk or scope -> `CLASSIFY`;
- insufficient understanding -> `INVESTIGATE`;
- architecture mismatch -> `PLAN` or `INVESTIGATE`;
- verification failure -> classify failure -> `INVESTIGATE` or `IMPLEMENT`;
- review defect -> `IMPLEMENT -> VERIFY -> REVIEW`;
- changed requirement -> compare the new authority with the active contract, mark only affected evidence `STALE`, then reclassify/replan;
- missing exact authority for a Critical action -> `WAIT_FOR_AUTHORIZATION`;
- unmet Definition of Done -> not `COMPLETE`.

Adaptive Fast-Exit compresses states; it does not erase repository instructions, scope control, meaningful verification, diff review, or evidence-based reporting. Eligibility comes from observed risk and clarity, never diff size. See the entrypoint for the exit conditions.

### Standard Engineering Mode
<!-- policy-id: standard-engineering-mode -->

Use the ordinary lifecycle proportionately for work that is not eligible for Fast-Exit and does not justify Team Mode. Planning may be internal or explicit according to risk. If investigation reveals a large formal requirement surface, dependency graph, multiple domains, High/Critical work units, phase/release gates, or resume risk, transition to Formal Spec Team Mode. If compilation proves the work small and tightly coupled, Team Mode may return here without discarding valid evidence.

### Formal Spec Team Mode

Formal specification execution remains the generic state model below. When orchestration complexity materially applies, load `formal-spec-team-mode.md` for Spec Compiler, work units, independent QA, Two-Key closure, cross-session state, and fresh release audit. Do not infer Team Mode only from requirement count, file count, or diff size.

## 4. Planning by risk

### Low

Hold a one-sentence change contract:

`intended behavior + allowed surface + proof`

Do not create a plan document unless the repository requires one.

### Moderate

Record a concise implementation sequence:

- affected files/modules;
- interfaces or consumers;
- intended behavior;
- tests/checks;
- dependencies between steps.

### High

Add:

- explicit behavioral invariants;
- failure/threat analysis;
- compatibility or rollback/roll-forward considerations;
- negative-path verification;
- required specialist review;
- release/merge gates.

### Critical

Verify exact current authorization for the consequential action and target.

If the user's current instruction already explicitly authorizes that exact action and target, the authorization requirement is satisfied. Complete the required gates and proceed without redundant confirmation.

If authority is broad, implied, stale, ambiguous, inherited from another scope, or does not identify the exact action/target, stop immediately before the consequential action and obtain exact authority.

“Prepare this for production” does not authorize deployment. “Deploy this exact release to production after the required checks pass” does.

## 5. Scope contract

Before non-trivial edits, know:

- requested outcome;
- explicit exclusions;
- intended implementation surface;
- allowed supporting changes;
- validation evidence.

Modify only what is:

- requested;
- required for correctness;
- required for compatibility;
- required for verification.

Do not opportunistically rename unrelated APIs, reformat unrelated files, replace libraries, migrate frameworks, or clean technical debt.

If adjacent debt blocks correctness, fix only the blocking portion and state why.

## 6. Formal specification execution
<!-- policy-id: formal-spec-execution -->

Use this mode when the user provides a formal `implementation.md`, remediation plan, audit plan, hardening plan, migration contract, or phased roadmap.

### Extract the contract

Separate:

- authoritative requirements;
- acceptance criteria;
- constraints/Decision Locks;
- background or rationale;
- suggestions;
- explicit deferrals.

### Build executable work

For each requirement, record:

- requirement identifier or concise name;
- dependencies;
- affected engineering surfaces;
- intended implementation;
- verification evidence;
- status.

Use distinct statuses:

- `NOT_STARTED`
- `IN_PROGRESS`
- `IMPLEMENTED`
- `VERIFIED`
- `STALE`
- `BLOCKED`
- `DEFERRED`
- `NOT_APPLICABLE`

Never collapse `IMPLEMENTED` into `VERIFIED`.

### Mid-execution requirement changes
<!-- policy-id: requirement-change -->

Treat a user correction, interruption, new constraint, or changed acceptance criterion as new current authority, not as noise to defer until the old plan finishes.

1. capture the new instruction and compare it with the active requirement ledger;
2. identify affected work units, dependencies, consumers, tests, and release claims;
3. preserve unaffected verified work;
4. mark only invalidated work/evidence `STALE`;
5. update acceptance criteria, scope, and risk;
6. replan and reverify the affected dependency path.

`STALE` means previously supported evidence no longer proves the current requirement. It is not failure and it does not erase historical evidence.

### Execute in dependency order

For each work unit:

1. gather current evidence;
2. confirm prerequisites;
3. implement the bounded change;
4. run the planned verification;
5. record result and unresolved issues;
6. advance only when dependencies permit.

### Phase closure versus release closure

`PHASE_VERIFIED != RELEASE_VERIFIED`

A verified phase may be closed while the release remains unverified.

Do not reopen a closed phase for speculative additional edge-case hunting without new evidence. New evidence, a cross-cutting regression, changed requirements, or final-audit findings may reopen it.

After all phases, perform a cross-cutting release audit for:

- requirement coverage;
- shared interfaces;
- security boundaries;
- migrations/data state;
- release gates;
- integration behavior;
- unresolved findings.

## 7. Authorization semantics
<!-- policy-id: authorization-semantics -->

Authorization is action-and-target specific.

Exact current authorization satisfies the authorization requirement for that exact action and target after its required gates.

Do not ask the user to reconfirm the same explicit instruction merely because the action is consequential.

Ask when authorization is:

- implied rather than explicit;
- broader than the concrete action;
- stale from an earlier scope;
- ambiguous;
- for a different target;
- insufficient to expand permissions or scope.

Authorization to prepare, review, validate, or make a branch does not imply authorization to merge, deploy, delete production data, send an external message, rotate a credential, or force-push.

## 8. Definition of Done

A task is complete only to the level supported by evidence.

At minimum:

- requested behavior/exclusions map to the actual diff;
- relevant checks were run after the final relevant edit;
- negative paths appropriate to risk were exercised;
- final status/diff is understood;
- high-risk profile obligations are satisfied;
- review findings are resolved or explicitly reported;
- no known blocker is hidden.

A blocking failure in a relevant required check prevents `COMPLETE` and yields `NOT_VERIFIED` or `BLOCKED`. A required check that is unavailable also blocks completion unless an equivalent, justified evidence source proves the requirement.

A failure may coexist with scoped completion only when evidence establishes that it is unrelated or pre-existing, its causality was investigated, and it does not invalidate the required evidence. Report it explicitly. An optional unavailable check is a limitation, not automatically a blocker. Avoid the contradictory state “complete but not verified.”

Keep lifecycle states distinct:

- implemented;
- locally verified;
- phase verified;
- release verified;
- reviewed;
- merged;
- released;
- deployed.

Report observed facts, inference, and unverified limitations separately.
