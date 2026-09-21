# Formal Spec Team Mode

Read this reference only when a formal specification is large, multi-phase, long-horizon, dependency-rich, specialist-sensitive, or requires distinct phase and release gates. Team Mode is orchestration discipline, not a requirement to maximize agent count.

## 1. Entry and source of truth
<!-- policy-id: formal-spec-team-mode -->

Enter from Standard Engineering Mode when evidence shows orchestration will reduce requirement loss or unsupported closure.

Positive signals include a large executable requirement surface, several dependent phases, multiple specialist domains, High/Critical work units, likely compaction/resume, distinct phase and release gates, or enough independent work that bounded ownership reduces integration risk. No numeric threshold decides alone.

Negative signals include a small clear contract with few executable requirements and no phase gates, one tightly coupled bounded feature, one domain, a short verification path, no material resume risk, and no independent-QA value beyond ordinary diff review. A formal file alone is never sufficient. Such work stays Standard Mode even when it is consequential and therefore ineligible for Fast-Exit.

Authority order:

1. current explicit user instruction;
2. original formal specification;
3. applicable repository instructions;
4. current source/config/test/runtime evidence;
5. derived requirement/work-unit state;
6. agent reports.

The original specification remains authoritative. Inventories, ledgers, maps, handoffs, and summaries are derived artifacts and must be reconciled back to it. Return to Standard Mode if compilation proves the work small and tightly coupled; escalate into Team Mode if ordinary work grows into the conditions above. Adaptive Fast-Exit never applies to a consequential Team Mode work unit merely because its patch is small.

## 2. Spec Compiler
<!-- policy-id: spec-compiler -->

Compile the specification before implementation in three loss-resistant passes.

### Pass 1 — Section Inventory

Inventory every meaningful source section by stable section ID and source heading/range. Classify each as requirement, acceptance criterion, Decision Lock, constraint, rationale/background, suggestion, deferral, release gate, verification instruction, or unknown/ambiguous. Record whether it is executable. Summarize locations; do not duplicate the entire specification. No section may silently disappear.

### Pass 2 — Requirement and acceptance extraction

Assign stable `REQ-###` IDs. Each executable requirement records:

- source section and concise requirement;
- acceptance criteria and constraints;
- attached Decision Locks;
- dependencies and affected surfaces;
- risk and specialist need;
- intended implementation/verification evidence;
- current state.

Allowed requirement states are `NOT_STARTED`, `READY`, `IN_PROGRESS`, `IMPLEMENTED`, `VERIFIED`, `STALE`, `BLOCKED`, `DEFERRED`, and `NOT_APPLICABLE`. Preserve explicit deferrals and unresolved ambiguity; do not relabel them as completed.

### Pass 3 — dependency graph and coverage reconciliation

Before coding, confirm:

1. every source section is classified;
2. every executable requirement has a work unit;
3. every acceptance criterion maps to a requirement;
4. every Decision Lock attaches to affected work;
5. every deferral remains visible;
6. every work unit maps to a requirement or explicit correctness need.

An orphan requirement has no work unit or evidence plan: mark planning `BLOCKED` until reconciled. An orphan change has no requirement/correctness justification: stop for scope-drift review. Maintain a scannable coverage matrix:

| Requirement | Source | Work Unit | Implementation | Evidence | Independent Review | Status |
|---|---|---|---|---|---|---|

## 3. Decision Locks

Decision Locks use `LOCKED`, `SUPERSEDED_BY_USER`, or `STALE`. Only current explicit user authority may supersede one. An agent may challenge a lock with evidence but cannot silently override it. QA and specialists cannot rewrite locks or acceptance criteria; they raise a finding or request clarification.

## 4. Orchestrator and work units

The Orchestrator/Tech Lead owns source reconciliation, Section Inventory, Requirement Ledger, locks, dependencies, work-unit graph, assignments, finding adjudication, phase/release state, and compact continuation state. It does not accept “done” as proof, become the default writer for every unit, or close a phase from builder claims.

Every non-trivial work unit records:

- `WORK-ID` and requirement IDs;
- objective and dependencies;
- allowed files/surfaces and forbidden changes;
- one active writer identity and read/write authority;
- expected artifacts and required verification;
- risk and conditional specialist need;
- state, current evidence, and stop conditions.

One writer owns a unit. Parallel builders are allowed only for dependency-independent, non-overlapping scopes with understood integration risk and file/worktree isolation where needed. Tightly coupled edits stay sequential. Default topology is one orchestrator, one active writer per ready unit, one independent QA function, zero or more relevant specialists, and one fresh release auditor at release closure—not maximum parallelism.

## 5. Independent QA and specialists

Independent QA receives original relevant requirements, acceptance, locks, repository instructions, actual diff/current code, tests, and builder evidence. Builder conclusions are claims, not the framing truth. QA maps acceptance to evidence, challenges the oracle, detects missing negative paths, test-cheating, stale verification, untested interfaces, and requirement omissions. For High/Critical units, derive expected behavior and negative paths before implementation when practical.

Specialists are conditional:

- security for auth/authz, RLS, tenants, secrets, webhooks, payments, untrusted input, privileges, uploads, external URLs, or sensitive infrastructure;
- database for migrations, schema/RLS, ownership/grants, `SECURITY DEFINER`, locks/backfills, compatibility, and rollback/roll-forward;
- frontend/browser for rendering, interaction, focus/keyboard, responsive/accessibility, browser APIs, or client/server state;
- performance for measurable latency, throughput, memory, bundle, or query goals using `BASELINE -> HYPOTHESIS -> CHANGE -> MEASURE -> COMPARE`.

Specialists own domain mechanics. The core retains scope, authorization, evidence, user-work safety, completion semantics, and Decision Locks.

## 6. Finding Ledger
<!-- policy-id: finding-ledger -->

Each finding records `FIND-ID`, source/reviewer, severity, requirement/work-unit linkage, description, evidence, proposed disposition, state, and closure evidence.

States are `OPEN`, `ACCEPTED`, `FIXED`, `VERIFIED_FIXED`, `REJECTED_WITH_EVIDENCE`, and `DEFERRED_AUTHORIZED`. Plain rejection, silent deletion, or “not important” without evidence is forbidden. Severity does not erase acceptance criteria.

If an equivalent finding returns twice, classify implementation defect, requirement ambiguity, architecture mismatch, broken oracle, environment problem, specialist disagreement, or stale evidence. A third equivalent cycle requires explicit adjudication—architecture change, oracle correction, clarification, escalation, authorized deferral, or user decision—before another blind patch.

## 7. Two-Key Phase Closure
<!-- policy-id: two-key-closure -->

For every Moderate/High/Critical Team Mode phase, `PHASE_VERIFIED` requires both:

1. **Implementation key:** intended diff/artifacts exist, required current tests pass, forbidden scope is absent, and builder evidence maps to requirements.
2. **Independent key:** QA/reviewer acceptance mapping passes, required negative paths pass, and required specialist evidence is resolved.

With either key missing, the phase may be `IMPLEMENTED` but not `VERIFIED`. A purely Low-risk phase may close without a second agent when independent review adds no material assurance and repository policy does not require it. Independence is about evidence and perspective, not agent theater.

`PHASE_VERIFIED != RELEASE_VERIFIED`. Phase evidence can be reopened only by new evidence, changed requirements, stale state, dependent regression, or release-audit finding—not speculative churn.

## 8. Requirement changes and cross-session state
<!-- policy-id: cross-session-state -->

On changed requirements, capture current authority, stop obsolete work safely, identify affected requirements/units/dependents, preserve unaffected `VERIFIED` work, mark only invalidated evidence `STALE`, update acceptance/locks/risk, replan the affected path, and rerun necessary integration/release evidence. Do not restart everything or preserve obsolete green checks.

For compaction/session boundaries, use the single canonical Compact State and resume protocol in `collaboration-state.md`. Do not create a repository artifact by default or duplicate a competing field list here. A genuine cross-session evaluation uses a fresh process/context.

## 9. Fresh Release Auditor
<!-- policy-id: fresh-release-auditor -->

After phase closure, a fresh auditor receives the original spec, repository instructions, base-to-HEAD diff, coverage matrix, locks, phase evidence, Finding Ledger, deferrals/blockers, and release gates. Do not prime it with “everything is complete”; orchestrator/builder conclusions remain claims.

Audit section coverage, executable requirements, acceptance evidence, orphan requirements/diffs, locks, High/Critical specialist obligations, Two-Key validity, findings/deferrals, phase/release distinction, migrations/data safety, integration behavior, stale evidence, and current release gates.

The only release verdicts are `RELEASE_VERIFIED`, `RELEASE_NOT_VERIFIED`, and `RELEASE_BLOCKED`. A cross-cutting defect prevents `RELEASE_VERIFIED` even when every phase was individually green.

## 10. Team Mode completion

Retain the universal `### Execution Summary`. Include only relevant Team Mode fields/sections: Policy, Mode, Risk, Status, Phases, Requirements, Verification, Findings, Deferred, Limitations, and Release Status. Execution Status still uses the universal controlled vocabulary; Release Status uses the three verdicts above. Never let model prose substitute for repository/test/review evidence.
