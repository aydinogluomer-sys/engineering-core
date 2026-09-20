# Implementation Contract: `engineering-core`

## 0. Contract status and semantics

This file is the execution contract for building and validating the reusable, repository-agnostic `engineering-core` Claude Code skill. It is not a product-feature plan and must not encode the identifiers, files, branches, commits, domain language, or acceptance criteria of any one repository.

Checklist semantics are strict:

- `[ ]` means unimplemented or not yet proven.
- `[x]` may be written only after the corresponding artifact exists and its stated validation evidence has been observed.
- `NOT RUN`, `PASS`, `FAIL`, and `BLOCKED` in the execution record describe actual command/check outcomes only.
- A behavioral instruction can guide Claude Code but cannot guarantee prevention. Deterministic blocking belongs to permissions, sandboxing, hooks, or another control plane.

This file must be updated incrementally as implementation proceeds. It must never claim success in advance.

## 1. Objective

Create `engineering-core`, a lean Claude Code skill that supplies a reusable engineering operating policy across unfamiliar repositories and future software-engineering tasks.

The skill must help Claude Code:

- select a workflow proportional to task complexity and consequence;
- discover and honor repository-local instructions before acting;
- ground decisions in source, tests, configuration, history, and runtime evidence;
- minimize scope and implement the smallest complete change;
- debug systematically rather than cycling through guesses;
- validate positive, negative, integration, and regression behavior in proportion to risk;
- escalate security-sensitive, data-sensitive, authentication, authorization, and billing work;
- use Git, secrets, subagents, specialist skills, external code-intelligence tools, and long-running state safely;
- review the final diff against the request and repository contract;
- make completion claims only from current evidence.

The runtime target is Claude Code. The package must follow current Claude Code Agent Skills conventions and use progressive disclosure.

## 2. System boundaries: four separate layers

The design must preserve these boundaries in both wording and package structure.

### 2.1 Skill: behavioral engineering policy

`engineering-core` guides classification, investigation, planning, implementation, debugging, testing, review, escalation, and completion. It does not itself enforce shell policy, install tools, grant permissions, or guarantee that unsafe actions cannot occur.

### 2.2 Hooks and control plane: optional deterministic enforcement

Claude Code permissions, sandboxing, managed policy, and `PreToolUse`/other hooks can deterministically allow, deny, ask, log, or validate actions. The skill may recommend or explain optional controls but must not install, enable, or modify them without an explicit request.

Mature command guards such as Safety Net or DCG may be suggested when a user wants deterministic destructive-command protection. They remain separately installed and independently trusted dependencies.

### 2.3 Observability: optional execution visibility

Hook/event telemetry, task views, logs, traces, and multi-agent dashboards expose what ran, failed, or delegated. Observability does not prove correctness and must not become a release gate unless the repository explicitly makes it one. Telemetry must avoid secrets and sensitive payloads.

### 2.4 Codebase intelligence: optional context providers

CodeGraph-family tools, Cartographer, Graphify, language servers, and similar systems can accelerate symbol discovery, dependency analysis, behavioral mapping, and blast-radius estimation. Their outputs are leads, not authority. Source files, repository instructions, tests, configuration, and version-control evidence remain the verification basis.

No external tool is a prerequisite for the base skill. Native `Read`, `Glob`, `Grep`, shell search, language tooling already present in the repository, and Git provide the fallback path.

## 3. Research synthesis

The package must synthesize principles, not concatenate commands or require the source systems.

### 3.1 Sources

Primary materials consulted for this contract:

- Official Claude Code skills: <https://code.claude.com/docs/en/skills>
- Official Claude Code best practices: <https://code.claude.com/docs/en/best-practices>
- Official Claude Code memory/instruction loading: <https://code.claude.com/docs/en/memory>
- Official Claude Code subagents and parallel agents: <https://code.claude.com/docs/en/subagents> and <https://code.claude.com/docs/en/agents>
- Official Claude Code hooks and permissions: <https://code.claude.com/docs/en/hooks-guide> and <https://code.claude.com/docs/en/permissions>
- Official Claude Code context guidance: <https://code.claude.com/docs/en/context-window>
- Anthropic Agent Skills authoring guidance: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
- Superpowers: <https://github.com/obra/superpowers>
- gstack: <https://github.com/garrytan/gstack>
- Trail of Bits skills/configuration: <https://github.com/trailofbits/skills> and <https://github.com/trailofbits/claude-code-config>
- Claude Code Safety Net: <https://github.com/yurukusa/claude-code-safety-net>
- Destructive Command Guard: <https://github.com/Dicklesworthstone/destructive_command_guard>
- Claude Code Hooks Mastery: <https://github.com/disler/claude-code-hooks-mastery>
- Multi-Agent Observability: <https://github.com/disler/claude-code-hooks-multi-agent-observability>
- CodeGraph: <https://github.com/colbymchenry/codegraph>
- Cartographer: <https://github.com/kingbootoshi/cartographer>
- Graphify: <https://github.com/Graphify-Labs/graphify>
- ClaudeKit engineering/debugging collections: <https://github.com/mrgoonie/claudekit-skills> and <https://github.com/duthaho/claudekit>
- Alireza Rezvani's skill collection: <https://github.com/alirezarezvani/claude-skills>

### 3.2 Adopted principles

| Source family | Principle adopted into `engineering-core` |
|---|---|
| Official Claude Code | Explore before broad edits; skip heavyweight planning for tiny clear changes; keep context bounded; respect additive and path-specific repository instructions; use subagents for isolated, high-volume work; verify with observable criteria. |
| Superpowers | Separate understanding, planning, implementation, verification, and review; use root-cause debugging; prefer minimal change; require evidence before completion; use fresh review where it adds confidence. |
| gstack | Review the product and engineering intent before polishing mechanics; use diff-first review, explicit ship gates, disciplined investigation, and role-specific specialist passes when warranted. |
| Trail of Bits | Build audit context from evidence; analyze blast radius; apply deeper security review only where risk warrants it; treat specialists as expertise, not generic ceremony. |
| Safety Net / DCG | Soft instructions are not deterministic prevention; destructive-command blocking and secret protection belong in optional hooks/permissions/control-plane mechanisms. |
| Hooks Mastery | Hooks are lifecycle-specific controls with explicit allow/deny/ask/log semantics; fail behavior, timeouts, scope, and test fixtures must be designed, not assumed. |
| Multi-Agent Observability | Correlate sessions, agents, tools, failures, and handoffs without confusing visibility with correctness; redact sensitive values. |
| CodeGraph / Cartographer / Graphify | Use relationship-aware and behavior-oriented maps to reduce context cost, but verify freshness and trace important claims back to source. |
| ClaudeKit collections | Use systematic debugging, root-cause tracing, defense in depth, verification before completion, and specialist routing for domain-specific work. |
| Alireza skill collection | Favor modular, discoverable specialist skills and reusable references instead of one monolithic prompt. |

### 3.3 Overlap and contradiction resolution

The core must resolve, rather than stack, competing prescriptions:

1. **Universal heavyweight process vs speed:** use task/risk classification. A typo or one-line local correction takes a fast path; uncertain, cross-boundary, or high-consequence work receives explicit investigation and planning.
2. **Always TDD vs risk-adaptive testing:** preserve the principle of proving behavior and reproducing defects, but do not require a failing test for changes where the repository has no practical test seam or the task is non-code. State the chosen proof and its limitation.
3. **Always delegate vs context efficiency:** delegate only bounded, independent work whose context isolation or specialization outweighs startup/synthesis cost. Keep coupled implementation in the primary context.
4. **Graph-first vs source-first:** query an available, fresh graph to find evidence; verify consequential conclusions in source/config/tests. Fall back natively without delay when unavailable or stale.
5. **Skill policy vs safety guarantee:** behavioral cautions stay in the skill; deterministic blocks are optional hooks/permissions. Never use words such as “impossible” for prompt-level safety.
6. **Broad autonomous execution vs authorization boundaries:** continue through safe in-scope work, but stop when a consequential user choice, new authority, destructive target, production mutation, or scope expansion is required.
7. **Independent review vs ritual:** require a fresh review for medium/high-risk changes or when requested; use a lightweight self-review for small low-risk changes.
8. **Many specialist skills vs conflicts:** repository/managed rules and explicit task constraints govern; the most specific relevant skill supplies domain mechanics; `engineering-core` retains cross-cutting evidence, safety, and completion policy.

## 4. Target package architecture

Create exactly:

```text
engineering-core/
|-- SKILL.md
|-- examples/
|   |-- high-risk-change.md
|   |-- large-spec-execution.md
|   |-- normal-feature.md
|   |-- removal-task.md
|   `-- small-fix.md
|-- references/
|   |-- operating-model.md
|   |-- repository-investigation.md
|   |-- implementation-debugging.md
|   |-- verification-review.md
|   |-- safety-profiles.md
|   |-- collaboration-state.md
|   |-- integrations.md
|   |-- source-synthesis.md
|   `-- evaluation-scenarios.md
`-- scripts/
    |-- validate_skill.py
    `-- test_validate_skill.py
```

No plugin manifest, active hook configuration, MCP configuration, vendored external tool, dependency manifest, asset, or installation script is authorized by this contract.

### 4.1 `SKILL.md`

The entrypoint must:

- use `name: engineering-core` and a discriminating description covering software-engineering implementation, debugging, refactoring, review, and release work;
- remain model-invocable so it can serve as a default engineering policy when relevant;
- avoid `allowed-tools`, model pinning, automatic tool installation, and deterministic-safety claims;
- put the universal operating loop and high-value invariants near the top for compaction resilience;
- route to references conditionally by task/risk class;
- remain below 200 lines and avoid duplicating detailed reference content.

### 4.2 References

Each reference owns one decision domain:

- `operating-model.md`: task classes, risk levels, fast/standard/high-risk paths, proportional plans, scope contract, Definition of Done framing.
- `repository-investigation.md`: instruction discovery/precedence, evidence hierarchy, bounded context, impact tracing, optional intelligence adapters and native fallback.
- `implementation-debugging.md`: minimum-correct change, preservation of existing behavior, debugging phases, hypothesis ledger, loop detection, failure classification.
- `verification-review.md`: risk-adaptive test matrix, negative paths, removal/completeness audits, diff-first review, spec-to-code compliance, independent review, release gates, evidence-based completion.
- `safety-profiles.md`: general security escalation plus database, authentication/authorization, billing, Git, secrets, destructive actions, external side effects.
- `collaboration-state.md`: subagent suitability, work partitioning, fresh-context review, specialist delegation, state ledger, checkpoint/resume, handoff evidence.
- `integrations.md`: explicit layer separation, optional hooks/control-plane patterns, observability event compatibility, codebase-intelligence provider protocol, degraded mode, trust and conflict rules.
- `source-synthesis.md`: concise provenance mapping and rejected/modified ideas so future maintainers understand why the core differs from source systems.
- `evaluation-scenarios.md`: repository-agnostic scenarios and expected policy outcomes for forward testing.

### 4.3 Structural and policy-lint validation scripts

Use Python standard library only.

`validate_skill.py` may check only statically observable properties:

- exact package tree and absence of active integration/config files;
- frontmatter validity, name/description, model-invocable policy, and no implicit permission grants;
- `SKILL.md` line ceiling;
- every conditional reference is linked and every local link resolves within the package;
- no unfinished scaffold markers;
- required capability coverage across the correct owning references;
- explicit separation of skill, hooks/control plane, observability, and codebase intelligence;
- external providers are described as optional with native fallbacks;
- no repository-specific task identifiers or concrete project coupling;
- no language claiming behavioral policy guarantees deterministic prevention;
- Python scripts import no third-party packages.

It must not claim to prove runtime model behavior, activation, security, root cause, absence of scope creep, or any other dynamic outcome. Its success label must be `Structural and Policy-Lint Validator` (or an unambiguous equivalent), not “semantic validity.” Deep behavioral evaluation belongs to scenario traces and live disposable-repository runs.

`test_validate_skill.py` must validate the real package and prove rejection of mutated temporary copies with at least:

- a missing reference;
- a broken local link;
- an oversized or monolithic entrypoint;
- an external tool made mandatory;
- a deterministic-safety guarantee placed in skill policy;
- missing fast path;
- missing high-risk profile;
- active hook/MCP configuration added to the package;
- invalid or over-broad frontmatter.

## 5. Behavioral architecture to implement

### 5.1 Universal operating loop

The core loop is:

`CLASSIFY -> DISCOVER -> INVESTIGATE -> PLAN -> IMPLEMENT -> VERIFY -> REVIEW -> COMPLETE`

The fast path may compress `INVESTIGATE` and `PLAN`, but may not skip repository instructions, scope checking, relevant verification, final diff inspection, or evidence-backed reporting.

Reclassification is allowed whenever new evidence changes scope or risk.

### 5.2 Task classification

At minimum classify:

- explain/inspect/review (read-only unless separately authorized);
- diagnose (find cause; do not silently implement unless requested);
- small correction;
- feature/change;
- refactor/removal/migration;
- test/build/release;
- security-sensitive or externally mutating work.

Classification determines whether implementation is authorized, not merely which procedure to use.

### 5.3 Risk classification

Define four levels:

- **Low:** localized, reversible, familiar pattern, narrow blast radius.
- **Moderate:** multiple files or interactions, meaningful regression surface, but contained and reversible.
- **High:** shared interfaces, concurrency, security boundaries, persistent data, auth, billing, infrastructure, releases, or hard-to-reverse behavior.
- **Critical:** production mutation, destructive data operation, irreversible external action, credential exposure, or uncertain authorization.

Risk is the maximum of consequence, reversibility, uncertainty, blast radius, privilege/data sensitivity, and verification difficulty. High/critical profiles cannot be downgraded solely because the diff is small.

### 5.4 Small-task fast path

For low-risk, well-specified, local work:

1. discover applicable instructions;
2. inspect the target and nearest precedent;
3. state or internally hold a one-sentence change contract;
4. make the smallest edit;
5. run the narrowest meaningful check plus diff review;
6. report evidence and limitations.

Do not manufacture design documents, subagents, broad repository maps, or full-suite runs unless the repository requires them.

### 5.5 Repository instruction discovery and precedence

Before edits, discover applicable managed/project/user instructions visible in the environment, root and nested `CLAUDE.md`/`CLAUDE.local.md`, `.claude/rules`, package-level instructions, contribution docs, build/test manifests, and relevant skill descriptions.

Resolve instructions by authority and specificity:

1. platform/managed safety and permissions;
2. explicit user objective, constraints, and authorization;
3. repository instructions applicable to the target path, with more local/specific guidance generally controlling mechanics;
4. specialist skill instructions for the domain;
5. `engineering-core` defaults;
6. optional tool suggestions.

Do not claim that concatenated repository instructions technically override one another; identify conflicts and use scope/specificity. Escalate consequential unresolved conflicts.

### 5.6 Evidence-first bounded investigation

Start with cheap evidence: status, file inventory, manifests, target symbols, nearest tests, recent relevant history, and call sites. Expand only when an unanswered question affects design, safety, or validation.

Maintain an evidence ledger for non-trivial work:

- requirement or hypothesis;
- observed source/test/config/runtime evidence;
- confidence and open question;
- affected surface;
- planned proof.

Stop acquiring context when the change contract, blast radius, and verification plan are supported. Do not read the entire repository by default.

Optional graph/map providers must pass availability, repository identity, freshness, and source-link checks. Their failure selects the native fallback; it does not block the task.

### 5.7 Proportional planning and scope discipline

- Low risk: one-sentence change contract.
- Moderate: concise file/behavior/test plan with dependencies.
- High: explicit invariants, threat/failure analysis, rollback or compatibility considerations, negative-path tests, release gates, and required approvals.
- Critical: pause before the consequential action and obtain explicit authority.

Plans must name intended outcomes and evidence, not speculative implementation detail. New unrelated defects become follow-up findings unless they block correctness or safety.

### 5.8 Minimum-correct implementation

Prefer the smallest change that fully satisfies the request and repository invariants. Reuse established abstractions when they fit; do not force reuse when it obscures correctness. Avoid opportunistic refactors, speculative extensibility, dependency additions, unrelated formatting, and generated-file churn.

Inspect the diff after coherent edit groups. Re-evaluate risk when the actual diff expands beyond the plan.

### 5.9 Systematic debugging, loop detection, and failure classification

Debug in phases:

1. reproduce and capture the exact failure;
2. localize the failing boundary and trace backward to the earliest violated invariant;
3. form a falsifiable hypothesis;
4. run the cheapest discriminating experiment;
5. implement the root-cause fix;
6. verify reproduction, regression, and adjacent negative paths.

Track attempts. Repeating the same action twice without new evidence triggers a tactic change. A third equivalent failure requires explicit classification before proceeding.

Classify failures as: code defect, test-oracle defect, environment/tooling, dependency/service, permissions/authorization, flaky/timing, missing prerequisite, scope conflict, or unknown. Never “fix” environment or oracle failures by weakening product behavior without evidence.

### 5.10 Verification and review

Testing scales with risk and changed behavior. Use the repository's real commands and start focused. Cover success, relevant failure, boundary, regression, and security cases. High-risk profiles require explicit negative paths.

Review in this order:

1. final status and diff, including generated/untracked files;
2. spec-to-code requirement matrix;
3. correctness and negative paths;
4. scope and removal/completeness audit;
5. security/privacy/compatibility/performance as applicable;
6. tests and release gates;
7. independent/fresh review when required.

Removal work must search for references, registrations, exports, flags, tests, docs, configuration, generated artifacts, and dead compatibility paths. “File deleted” is not completion evidence.

### 5.11 High-risk profiles

- **Security:** threat boundary, untrusted input, secret handling, dependency provenance, unsafe deserialization/injection, authorization enforcement, logging/redaction, fail-open behavior.
- **Database:** migration ordering, locks, compatibility window, backfill/idempotency, rollback limits, constraints, tenant/RLS behavior, restore evidence, production separation.
- **Authentication/authorization:** server-side enforcement, session/token lifecycle, privilege escalation, default-deny, tenant isolation, revocation, enumeration, CSRF/replay as applicable.
- **Billing/payments:** money units/rounding, idempotency, webhook authenticity/replay, duplicate/out-of-order events, state-machine transitions, reconciliation, refunds, auditability, test/live separation.

Use a specialist security review when exposure or uncertainty warrants it. The core should route to an available trusted specialist skill; it must not pretend to replace domain expertise.

### 5.12 Git and secret safety

Inspect worktree and target paths before destructive or broad Git/file actions. Do not discard, overwrite, stash, reset, clean, rewrite history, force-push, or expose user work without explicit scope and authority. Prefer recoverable actions and exact paths.

Never print, commit, transmit, or place secrets in prompts, logs, diffs, fixtures, or observability events. Use placeholders and environment-variable names. Treat secret discovery as sensitive evidence and redact it immediately.

### 5.13 Delegation, specialist skills, and conflicts

Delegate only when work is bounded, separable, and benefits from specialization, parallelism, or context isolation. Define deliverable, allowed scope, evidence, and stop condition. Avoid multiple agents editing overlapping files without worktree isolation or explicit ownership.

For medium/high-risk changes, use an independent fresh reviewer when available and proportionate. The reviewer receives the request, relevant repository instructions, and actual diff/evidence—not the implementer's conclusions alone.

Invoke specialist skills only when relevant and available. Do not install tools or skills merely because the core mentions them. Resolve conflicts using the precedence in Section 5.5; preserve cross-cutting safety/evidence rules while allowing the specialist to control domain mechanics.

### 5.14 Long-horizon state

For work likely to span compaction, sessions, or many gates, maintain a compact state record using an existing task system or a user/repository-approved file. Do not create repository artifacts by default.

Record objective, authorization boundary, decisions, evidence, modified files, commands/results, open failures, next action, and stop conditions. On resume, verify repository state instead of assuming the record is current.

### 5.15 Release gates and Definition of Done

Release/merge/deploy actions require explicit authorization and repository-defined gates. Separate “code implemented,” “locally verified,” “reviewed,” “merged,” and “deployed.” Never collapse them into one success claim.

Definition of Done is evidence-based:

- requested behavior and exclusions map to the diff;
- relevant tests/checks passed after the final edit;
- negative paths appropriate to risk were exercised;
- final diff/status is understood and scoped;
- high-risk profile obligations are satisfied;
- fresh review findings are resolved or reported;
- no known blocker is hidden;
- claims distinguish observed facts, inference, and unverified limitations.

## 6. Implementation phases and gates

### Phase 1 — Remove the incorrect artifact

Tasks:

1. Delete the prior repository-specific skill package.
2. Verify no product-specific identifiers remain anywhere in the workspace artifacts.

Dependencies: none.

Gate: workspace contains only this implementation contract before the new package is authored.

### Phase 2 — Author the policy architecture

Tasks:

1. Create the exact package tree in Section 4.
2. Write a lean `SKILL.md` router with the universal loop, fast path, mandatory escalation triggers, and conditional reference links.
3. Write each reference with single ownership and no duplicated full procedures.
4. Encode all behavior in Section 5 and all boundary distinctions in Section 2.
5. Add source synthesis with explicit adopted, modified, and rejected patterns.

Dependencies: Phase 1 and the research in Section 3.

Gate: manual traceability review maps every requested capability to one owning file and a route from `SKILL.md`.

### Phase 3 — Implement deterministic package validation

Tasks:

1. Implement `scripts/validate_skill.py` as specified in Section 4.3.
2. Implement mutation-based regression tests.
3. Ensure scripts are standard-library only and do not alter the package during validation.

Dependencies: Phase 2 package shape/content.

Gate: validator passes the real package and rejects every required invalid fixture.

### Phase 4 — Static validation

Run, record, and require success from:

```text
python engineering-core/scripts/validate_skill.py engineering-core
python engineering-core/scripts/test_validate_skill.py
python -m py_compile engineering-core/scripts/validate_skill.py engineering-core/scripts/test_validate_skill.py
```

Also inspect:

- exact file inventory and hashes;
- unresolved local Markdown links;
- unfinished markers;
- secrets/credential-like literals;
- unexpected binary/cache/config files;
- `SKILL.md` line count;
- absence of product-specific coupling.

Dependencies: Phase 3.

Gate: every executed check is recorded with observed output; failures remain failures until rerun successfully after refinement.

### Phase 5 — Behavioral and adversarial evaluation

Evaluate at least:

- read-only explanation versus authorized implementation;
- trivial low-risk correction using the fast path;
- moderate multi-file change;
- ambiguous bug requiring reproduction;
- deletion/removal completeness;
- unavailable or stale graph provider with native fallback;
- conflicting repository and specialist instructions;
- repeated failed attempts and tactic change;
- dirty worktree/destructive Git pressure;
- secret exposure pressure;
- database migration/backfill;
- authentication/authorization change;
- billing/webhook change;
- security review escalation;
- subagent task that is suitable and one that is coupled/unsuitable;
- long-horizon resume with stale state;
- failed/flaky/environmental test classification;
- release request with missing gate or authority;
- completion claim with stale or absent evidence.

Use isolated, disposable fixtures. A live Claude Code forward evaluation is optional and must be read-only or separately authorized; inability to run it must be recorded as `BLOCKED` or `NOT RUN`, never converted to `PASS`.

Dependencies: Phases 2-4.

Gate: every scenario has an observed or manually traced outcome, with critical failures refined and rerun.

### Phase 6 — Final audit and refinement

Tasks:

1. Perform diff-first review of the skill package itself.
2. Compare artifacts against Sections 1-5 and the user's required capability list.
3. Check that optional integrations remain optional and the four layers remain distinct.
4. Check instruction conflicts, duplication, routing gaps, and context cost.
5. Mark an acceptance item `[x]` only with cited evidence from executed checks.
6. Populate the execution record without rewriting historical failures.

Dependencies: all prior phases.

Gate: no unresolved critical finding; any limitation is explicit.

## 7. Acceptance criteria

- [x] Package is named `engineering-core` and contains the exact authorized tree.
- [x] `SKILL.md` is lean, model-invocable, under 200 lines, and routes details progressively.
- [x] Task and four-level risk classification drive a genuine small-task fast path and proportional planning.
- [x] Repository instruction discovery, additive/specific precedence, and conflict escalation are accurate for Claude Code.
- [x] Investigation is evidence-first, bounded, and supports optional graph/map providers with native fallbacks.
- [x] Scope discipline and minimum-correct implementation reject opportunistic expansion without blocking safe in-scope work.
- [x] Debugging includes reproduction, hypothesis testing, root-cause correction, loop detection, and failure classification.
- [x] Verification covers risk-adaptive positive, negative, boundary, regression, removal, and release behavior.
- [x] Security, database, authentication/authorization, and billing profiles contain domain-specific escalation and tests.
- [x] Git/destructive-action and secret handling policies preserve authorization and redaction boundaries.
- [x] Subagent delegation, independent review, specialist routing, work isolation, and conflict resolution are proportional.
- [x] Long-horizon state is compact, resumable, verified on return, and does not create repository files by default.
- [x] Final review is diff-first and includes spec-to-code, completeness/removal, and evidence-based Definition of Done.
- [x] Skill, optional hooks/control plane, optional observability, and optional codebase intelligence are clearly separated.
- [x] External systems are optional and never installed, invoked, or required merely by loading the skill.
- [x] Validator passes and all required mutation tests prove it fails closed on malformed packages.
- [x] Adversarial evaluation covers every scenario family in Phase 5.
- [x] No repository-specific concepts, unfinished markers, secrets, active integrations, or unexpected files remain.

## 8. Baseline execution record — pre-refinement

Historical record only. This section describes the validated pre-refinement baseline and is retained for audit history. The current refined package shape and validation evidence are recorded in Section 10.5 and supersede this section for present-state claims.

Record only observed results.

| Check | Status | Evidence |
|---|---|---|
| Prior artifact removal | PASS | Verified the obsolete package contained no remaining files, removed its empty directories, and listed the workspace with only `implementation.md`. |
| Package inventory | PASS | Historical pre-refinement inventory contains exactly 12 authorized files: `SKILL.md`, nine references, and two Python scripts; validator rejects extras. |
| Frontmatter and line budget | PASS | Bundled `quick_validate.py` returned `Skill is valid!`; `SKILL.md` is 61 lines and has only `name` and `description`. |
| Progressive-disclosure links | PASS | Semantic validator resolved all local links and confirmed `SKILL.md` routes to every reference. |
| Capability traceability | PASS | Manual ownership matrix below maps every required capability to one primary reference and an entrypoint route. |
| Historical baseline validator | PASS | Before the refinement contract, the initial validator failed because a guarantee detector matched a negated statement; its narrowed rerun passed. That former “semantic” label is superseded by the L1/L2 Structural and Policy-Lint Validator and is not behavioral evidence. |
| Validator regression tests | PASS | Initial run had 9 passes/3 failures from the detector and broken-link fixture defects. After fixes, two final runs passed all 12 tests, including every required mutated package. |
| Python syntax | PASS | `python -m py_compile engineering-core/scripts/validate_skill.py engineering-core/scripts/test_validate_skill.py` exited 0; generated cache was removed and a no-bytecode rerun left none. |
| Placeholder/secret/binary/config scan | PASS | `rg` scans reported clean Markdown placeholders and secret-like literals; inventory found no active hooks, MCP/settings/plugin/dependency configuration or unexpected binaries. |
| Product-coupling scan | PASS | Explicit scan of `implementation.md` and `engineering-core` for identifiers from the discarded example returned `PRIOR_PROJECT_COUPLING_SCAN_CLEAN`; validator also applies generic coupling patterns. |
| Behavioral scenario trace | PASS | Manual policy trace covered all 28 scenarios with no critical-failure path; grouped evidence below. This is explicitly a manual trace, not a live model run. |
| Optional live Claude Code evaluation | NOT RUN | Optional forward-model run was not used; avoiding unbounded external model cost does not weaken the deterministic/static checks or manual trace, but live behavioral variance remains unmeasured. |
| Final diff-first audit | PASS | First run failed because its predicate matched the explanatory literal `` `[ ]` ``; that failure is retained here. The refined full rerun passed validator + 12 tests, obsolete-package absence, actual unchecked-item scan, pending-record scan, prior-project coupling scan, cache scan, and exact hash inventory. Workspace is not a Git repository, so file inventory/hashes and full content review are the artifact-level equivalent; no VCS diff claim is made. |

## 9. Evidence appendices

### 9.1 Capability ownership trace

| Capability family | Primary owner | Entrypoint route / evidence |
|---|---|---|
| Task/risk classification, fast path, proportional planning, scope, Definition of Done | `references/operating-model.md` | `SKILL.md` operating loop, invariants, fast path, and route. |
| Instruction discovery/precedence, evidence-first investigation, bounded context, impact, graph fallbacks | `references/repository-investigation.md` | Conditional unfamiliar/cross-file/integration route. |
| Minimum-correct implementation, systematic debugging, attempt loops, failure classification | `references/implementation-debugging.md` | Conditional bug/failure/implementation route. |
| Adaptive and negative-path tests, diff/spec/removal reviews, fresh review, release gates | `references/verification-review.md` | Moderate/high-risk, removal, review, release, and completion route. |
| Security escalation, database, auth, billing, Git, secrets, external actions | `references/safety-profiles.md` | High-risk trigger route and entrypoint safety boundary. |
| Subagents, specialists, conflicts, independent review, long-horizon state/resume | `references/collaboration-state.md` | Delegation/state conditional route. |
| Hooks/control plane, observability, codebase intelligence, degraded mode | `references/integrations.md` | Explicitly conditional integration route; four-layer table. |
| Provenance and overlap resolution | `references/source-synthesis.md` | Maintainer-only route. |
| Behavioral/adversarial coverage | `references/evaluation-scenarios.md` | Maintainer-only route with 28 cases and critical failures. |

### 9.2 Manual adversarial trace

| Scenario group | Cases | Result | Policy evidence |
|---|---:|---|---|
| Authorization, fast/standard paths, diagnosis, reproduction, removal | 1-6 | PASS (manual trace) | Task class table, fast path, debugging phases, completeness audit. |
| Optional providers and instruction/skill conflicts | 7-10 | PASS (manual trace) | Provider trust/native fallback plus authority/specificity conflict rules. |
| Loop and failure classification | 11-13 | PASS (manual trace) | Attempt ledger, two-attempt tactic change, third-failure classification, oracle safeguards. |
| Git and secret safety | 14-15 | PASS (manual trace) | Exact-target/user-work policy and secret redaction/rotation boundary. |
| Database, auth, billing, and security escalation | 16-19 | PASS (manual trace) | Four high-risk profiles with explicit domain negative paths. |
| Suitable/unsuitable delegation and fresh review | 20-22 | PASS (manual trace) | Delegation suitability, isolation/ownership, unprimed review contract. |
| Long-horizon resume, hook denial, missing observability | 23-25 | PASS (manual trace) | State revalidation, no hook bypass, observability degraded mode. |
| Release authority, failed gates, stale completion evidence | 26-28 | PASS (manual trace) | Separate release mutations, failure disclosure, post-final-edit evidence rule. |
| Exact/ambiguous authority and tiny dangerous diffs | 29-31 | PASS (manual trace) | Exact-current authorization examples plus maximum-dimension risk and one-line high-risk examples. |
| Phase closure and cross-cutting reopening | 32-33 | PASS (manual trace) | Formal-spec ledger distinguishes phase/release verification and permits reopening only from new evidence. |
| Validator claims, specialist boundaries, activation, compaction | 34-37 | PASS (manual trace) | L1-L5 hierarchy, additive core+specialist rule, non-guaranteed activation guidance, and stale-evidence resume protocol. |

## 10. Refinement execution contract

This section governs the repository-agnostic refinement pass requested after the validated baseline above. Earlier evidence remains historical; it does not pre-validate the new requirements below. New acceptance items begin unchecked and may change only after the cited level of evidence has actually run.

### 10.1 Top-level architecture

The refinement preserves the existing progressive-disclosure architecture:

1. **Lean dispatcher:** `SKILL.md` retains the compact lifecycle, universal invariants, escalation triggers, and conditional routes needed to survive compaction.
2. **Runtime policy references:** the existing nine references remain the authoritative policy modules. Formal specification execution belongs in `operating-model.md`; provider trust and optional activation guidance belong in `integrations.md`; no new reference is authorized.
3. **Worked examples:** exactly five new files under `examples/` demonstrate adaptive behavior without becoming mandatory templates.
4. **Structural and Policy-Lint Validator:** the existing standard-library validator checks only statically observable package and policy properties and authorizes exactly the five examples.
5. **Evaluation stack:** manual scenario traces and, when safe and available, bounded live Claude Code runs evaluate behavior without converting lower-level evidence into higher-level claims.

The four system layers remain separate: skill policy is behavioral guidance; hooks/control-plane controls are optional deterministic enforcement; observability provides execution visibility; codebase-intelligence systems are optional context providers.

### 10.2 Evidence hierarchy

| Level | Evidence | Permitted claim |
|---|---|---|
| L1 | Structural validation: tree, frontmatter, links, line limits, imports | The package has the expected static shape. |
| L2 | Policy lint: required sections, optionality language, obvious forbidden claims/coupling | The written policy contains selected guardrails and no detected lint violation. |
| L3 | Deterministic/manual scenario evaluation | The documented policy resolves the evaluated scenarios as recorded. |
| L4 | Bounded live Claude Code runs in disposable repositories | The tested Claude/runtime combination exhibited the recorded behavior in those fixtures. |
| L5 | Field evaluation across real tasks and time | The skill's operational effectiveness is supported within the observed population and period. |

No lower level may claim a higher-level outcome. In particular, L1/L2 cannot prove activation, runtime compliance, security, correct root-cause discovery, or absence of scope creep.

### 10.3 Refinement phases and dependencies

#### R1 — Baseline and provenance audit

- Inventory the current package and preserve validated architecture unless new evidence requires a change.
- Correct provenance to `colbymchenry/codegraph`, `kingbootoshi/cartographer`, and `Graphify-Labs/graphify`.
- Rewrite the source comparison so every source family records source, observed principle, adopted/modified/rejected decision, implementation location, and rationale.

Gate: source identities are correct and the final comparison covers every named source family.

#### R2 — Runtime policy refinement

- Add formal specification execution, requirement states, dependency-aware work units, phase closure, release closure, and evidence-governed reopening to `operating-model.md`.
- Make authorization exact: current explicit authority for the exact action and target permits execution after required gates; broad, implied, stale, ambiguous, or differently scoped intent does not.
- Expand risk dimensions and examples; the highest applicable dimension controls and downward reclassification requires evidence.
- Add explicit lifecycle backward transitions and preserve the distinction between compressed and erased phases.
- Strengthen provider trust, specialist boundaries, activation semantics, long-horizon state, and compaction-resilient invariants without duplicating modules.

Gate: every required runtime rule has one primary owner and an entrypoint route.

#### R3 — Worked examples

Create exactly:

- `examples/small-fix.md`
- `examples/normal-feature.md`
- `examples/high-risk-change.md`
- `examples/removal-task.md`
- `examples/large-spec-execution.md`

Each example must show concrete decisions, evidence, adaptive context/planning/testing, and completion reporting. Examples illustrate policy; they do not override repository instructions or authorize actions.

Gate: all five examples satisfy their scenario-specific requirements and are routed from the lean entrypoint without eager loading.

#### R4 — Validator correction

- Rename its claim to **Structural and Policy-Lint Validator**.
- Authorize exactly the five example paths.
- Check structure, frontmatter, links, line budget, required modules/examples, optional integrations/native fallback language, placeholders, obvious contradictions/coupling/deterministic claims, and standard-library imports.
- Prefer explicit headings/markers and narrowly scoped checks over fragile deep semantic regexes.
- Add mutation tests for missing examples, stale provenance, validator overclaiming, required external tools, activation guarantees, and other high-value static regressions.

Gate: L1/L2 checks pass the real package and reject all intended mutations without claiming L3-L5 outcomes.

#### R5 — Adversarial and live evaluation

- Expand the manual suite with redundant confirmation, ambiguous production intent, tiny dangerous diff, stale phase state, new cross-cutting evidence, static-validator overclaim, specialist conflict, activation ambiguity, and compaction/resume with stale tests.
- If Claude Code is available and a bounded run is safe, exercise disposable fixtures covering at least: trivial fast path, moderate multi-file work, high-risk security/auth/billing reasoning, dirty worktree preservation, unavailable graph fallback, and formal specification execution.
- Bound model, permissions, fixtures, time, and spend. Stop rather than repeat an unproductive run. Record each case as `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN` from observed evidence only.

Gate: L3 is complete; L4 is reported exactly to the extent executed.

#### R6 — Final audit and refinement

- Run the structural/policy-lint validator, mutation tests, syntax checks, inventory/link/placeholder/secret/config/coupling scans, and line-count checks.
- Audit context cost, duplicated policy, source-to-policy traceability, all acceptance items, and exact package tree.
- Distinguish changed artifacts, static evidence, behavioral evidence, live-evaluation limitations, and quality assessment.
- Refine any failed critical scenario and rerun the affected gate; retain failure history.

Gate: no unresolved critical finding and every completion claim names its evidence level.

### 10.4 Refinement acceptance criteria

- [x] Correct CodeGraph, Cartographer, and Graphify provenance appears everywhere, with a decision-and-location comparison for every requested source family.
- [x] The exact package tree contains the prior files plus exactly five authorized example files and no active integration/config artifact.
- [x] `SKILL.md` remains lean and compaction-resilient, routes examples conditionally, and preserves every universal invariant.
- [x] Formal specification execution is first-class policy with requirement states, dependencies, work units, phase verification, release verification, unresolved ledger, and evidence-controlled reopening.
- [x] Authorization semantics avoid redundant confirmation for exact current authority and stop before broad, implied, stale, ambiguous, or differently scoped consequential actions.
- [x] Risk uses maximum consequence, reversibility, uncertainty, blast radius, privilege sensitivity, data sensitivity, external side effects, and verification difficulty; a small diff never implies low risk.
- [x] Lifecycle backward transitions cover new evidence, insufficient understanding, architectural mismatch, verification failure, review defects, missing Critical authority, and unmet Definition of Done.
- [x] Provider trust checks availability, repository identity, freshness, provenance/source location, and relevant language/artifact coverage, with source/config/test verification and native fallback.
- [x] Optional activation guidance distinguishes probabilistic skill-description relevance from stronger but non-guaranteed `CLAUDE.md` routing and never modifies repository instructions automatically.
- [x] Specialist examples preserve `engineering-core` cross-cutting policy while delegating domain mechanics and resolving conflicts by authority, scope, and specificity.
- [x] All five worked examples demonstrate the required adaptive process and negative exclusions.
- [x] The validator is explicitly limited to L1/L2, uses the name Structural and Policy-Lint Validator, and does not claim behavior, activation, security, root cause, or impossible scope control.
- [x] Validator tests cover the exact expanded tree and new epistemic/provenance/activation regressions.
- [x] Manual adversarial evaluation includes all baseline and newly requested cases with observed L3 outcomes.
- [x] Bounded live Claude Code evaluation covers all six required families, or each unexecuted family is accurately marked `BLOCKED`/`NOT RUN` with no inflated claim.
- [x] Final context-cost and duplication audit finds no unnecessary module, repeated full workflow, or eager-loaded example/reference.
- [x] Final audit reports exactly which evidence levels ran and leaves L5 unclaimed unless genuine field evidence exists.

### 10.5 Refinement execution record

| Check | Status | Evidence |
|---|---|---|
| Provenance and source comparison | PASS | Markdown/source scan found the intended `colbymchenry/codegraph`, `kingbootoshi/cartographer`, and `Graphify-Labs/graphify` sources; the source-to-policy table covers all requested families with observed principle, decision, location, and rationale. |
| Runtime policy traceability | PASS | Manual trace and policy-lint inspection located formal-spec execution, exact authorization, maximum-dimension risk, lifecycle recovery, provider trust, activation guidance, specialist boundaries, and stale-state recovery in their designated owners. |
| Five worked examples | PASS | Exact-tree validation found only the five authorized examples; policy lint checked their required scenario markers and every example is conditionally linked from the 62-line entrypoint. |
| Structural and Policy-Lint Validator | PASS | First refinement run failed with six findings and the second with one false-positive coupling match; both failures were retained in tool output. After replacing fragile generic phrase checks, the final command returned `PASS: Structural and Policy-Lint Validator found no configured violations`. |
| Validator mutation tests and syntax | PASS | Final run passed 16/16 mutation tests, `py_compile` exited 0, and the skill-creator `quick_validate.py` returned `Skill is valid!`; generated bytecode cache was moved out of the package afterward. |
| Manual adversarial evaluation | PASS | L3 manual trace covers all 37 documented scenarios, including the nine refinement cases; this is policy evaluation, not live model proof. |
| Live Claude Code evaluation | BLOCKED | Claude Code 2.1.271 was run once against an isolated six-case dirty-worktree fixture using Haiku, plan mode, no persistence, and a $0.15 cap. It spawned one exploration agent, reached $0.219564, exited 1 with `budget_exhausted`, and returned no scenario result. Per the stop rule it was not retried; all six L4 cases remain unscored. The fixture was moved intact to the user temp directory. |
| Final inventory, coupling, secret, config, context-cost, and duplication audit | PASS | Final audit found 17 authorized files, 62 `SKILL.md` lines, clean project-coupling/placeholder/credential-pattern/active-config scans, resolved links, no package cache, and SHA-256 inventory. Manual ownership review found no new reference, repeated full workflow, or eagerly loaded example. |

### 10.6 Final evidence audit

| Level | Status | Scope |
|---|---|---|
| L1 structural | PASS | Exact tree, frontmatter, links, line budget, imports, syntax, hashes, and absence of unexpected files. |
| L2 policy lint | PASS | Required policy/example markers, optionality and layer boundaries, stale provenance, activation/deterministic overclaims, placeholders, obvious coupling, and dependency constraints. |
| L3 scenario | PASS | Manual trace of all 37 repository-agnostic scenarios. |
| L4 live Claude behavior | BLOCKED | One bounded six-family run exhausted its cap before returning a result; no family is scored. |
| L5 field evaluation | NOT RUN | No longitudinal real-task population was evaluated, so no field-effectiveness claim is made. |

Quality assessment: the package is structurally complete and internally coherent at L1-L3. Its runtime effectiveness and activation reliability remain deliberately unscored until successful L4 runs and longitudinal L5 evidence exist.

## 11. Production Hardening and L4 Closure Contract

This contract governs the post-`9909598` hardening pass. It preserves the existing state machine, progressive-disclosure architecture, exact inner-package tree, five worked examples, optional-integration boundary, and all historical evidence—including the prior `budget_exhausted` L4 result. New evidence is appended; old outcomes are never rewritten.

### 11.1 Baseline

- Repository: `aydinogluomer-sys/engineering-core`
- Baseline branch/commit: `main` at `9909598cc6294b211c3589c68cc0b47117f972b5`
- Pre-existing modifications: none (`git status --short` produced no entries)
- Existing GitHub workflow directory: absent
- Inner runtime package: 17 files; `SKILL.md` 62 lines
- Existing evidence: L1/L2/L3 PASS, prior combined L4 attempt BLOCKED by budget exhaustion, L5 NOT RUN

### 11.2 Workstreams

#### H1 — Positive standard-library import classification

- **Objective:** make “stdlib-only” a positive, complete classification claim for the supported Python floor.
- **Likely files:** `engineering-core/scripts/validate_skill.py`, `engineering-core/scripts/test_validate_skill.py`, `README.md`, CI workflow.
- **Dependencies:** Python floor decision and current runtime metadata.
- **Tasks:** parse imports with AST; classify each root as future/builtin, standard library via `sys.stdlib_module_names`, legitimate local module, or unknown external; never import candidate modules or execute package code; add acceptance/rejection mutations.
- **Gate/evidence:** arbitrary unknown, NumPy, HTTPX, Requests, and Pydantic imports fail with actionable errors; `os`, `pathlib`, `urllib.parse`, `typing`, `__future__`, and local `validate_skill` imports pass; tests run on the minimum and current CI versions.
- **Failure semantics:** unsupported interpreter or unclassifiable external import fails validation; no claim of compatibility for an untested Python version.

#### H2 — Conditional frontend, dependency, and performance profiles

- **Objective:** add missing engineering verification mechanics without making ordinary work heavyweight.
- **Likely files:** `engineering-core/references/verification-review.md`, `engineering-core/references/implementation-debugging.md` only if ownership requires it, `engineering-core/examples/normal-feature.md`, evaluation scenarios, validator markers.
- **Dependencies:** existing risk model and small-task fast path.
- **Tasks:** add stable headings `Frontend / browser verification`, `Dependency changes`, and `Performance work`; keep browser tools optional; cover task-relevant UI negative states, dependency necessity/compatibility/lockfile/supply-chain concerns, and `BASELINE -> HYPOTHESIS -> CHANGE -> MEASURE -> COMPARE`.
- **Gate/evidence:** markers survive validation, adversarial scenarios cover low and elevated cases, and the trivial typo scenario still routes through the fast path without browser/dependency/performance ceremony.
- **Failure semantics:** unavailable optional tooling is reported, not fabricated or auto-installed; required evidence remains blocking when no valid alternative exists.

#### H3 — Requirement-change and completion state semantics

- **Objective:** make mid-execution changes selectively invalidate evidence and make blocking failures incompatible with `COMPLETE`.
- **Likely files:** `SKILL.md`, `references/operating-model.md`, `references/verification-review.md`, `references/collaboration-state.md`, `examples/large-spec-execution.md`, `examples/high-risk-change.md`, evaluation scenarios, validator markers.
- **Dependencies:** formal-spec ledger, lifecycle states, exact authorization semantics.
- **Tasks:** add `STALE` as the smallest state extension; capture new authority, compute affected/downstream work, preserve unaffected verified units, invalidate only changed assumptions, reclassify/replan selectively; distinguish blocking relevant, unrelated/pre-existing, optional unavailable, and required unavailable failures.
- **Gate/evidence:** policy and examples show selective reopening; a blocking required failure yields `NOT_VERIFIED`/`BLOCKED`, never `COMPLETE`; unrelated proven failures may permit scoped completion only when disclosed and non-invalidating.
- **Failure semantics:** absent required evidence blocks completion; uncertainty about causality remains `NOT_VERIFIED` rather than being labeled unrelated.

#### H4 — Expanded L3 adversarial evaluation

- **Objective:** exercise all new policy surfaces without mislabeling policy reasoning as live behavior.
- **Likely files:** `engineering-core/references/evaluation-scenarios.md`, `implementation.md` evidence record.
- **Dependencies:** H2-H3 policy text.
- **Tasks:** add at least 19 scenarios covering browser/UI, dependencies, performance, requirement changes, and completion/failure semantics; each records pressure, classification, action, non-action, completion state, and L3 evidence level; retain all prior cases.
- **Gate/evidence:** manual policy trace maps every scenario to its owning rule with no critical contradiction.
- **Failure semantics:** unresolved policy conflict is FAIL and prevents the corresponding acceptance item from closing.

#### H5 — Repeatable isolated L4 harness

- **Objective:** obtain genuine per-case live Claude Code evidence and prevent one costly case from consuming all results.
- **Likely files:** root `evals/`, `docs/l4-evaluation.md`, `.gitignore`, README; never the inner package for harness code.
- **Dependencies:** installed `claude --help` capabilities, H1-H4 stable policy, disposable local Git fixtures.
- **Tasks:** run one scenario per process/repository; install the skill locally in each fixture; distinguish explicit from natural activation; use self-contained fixtures; capture structured output, exit/cost/timeout, Git diff/status, tests, hashes, files, and assertions; redact secrets; bound per-case/total cost, timeout, and retries; classify failures.
- **Gate/evidence:** all six core families are independently attempted and receive exact `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`; at least one actual scored case is required before claiming any L4 validation.
- **Failure semantics:** timeout/budget/tooling/permission/fixture/scoring failures remain per-case and do not automatically stop later cases within the total budget; no repeated retry without a changed strategy.

#### H6 — Public repository CI and hygiene

- **Objective:** make cloning, static validation, and contribution reproducible without secrets or runtime-package pollution.
- **Likely files:** `.github/workflows/validate.yml`, optional root validation script, `README.md`, `docs/l4-evaluation.md`, `.gitignore`.
- **Dependencies:** Python floor, final commands, official current Action versions.
- **Tasks:** add push/PR/manual static CI over Linux/Windows and minimum/current Python; run directly against repository files; add repository-level Markdown-link/placeholder/hygiene checking separately from inner-package validation; document installation, evidence levels, L4 use/status, and development commands with the real clone URL.
- **Gate/evidence:** workflow YAML and referenced paths inspect cleanly; local CI-equivalent commands pass; hosted CI remains `NOT RUN` until an authorized push creates a run.
- **Failure semantics:** workflow authoring or local equivalence is not hosted-CI PASS; no secret-dependent L4 on push/PR.

#### H7 — Final cross-cutting audit

- **Objective:** verify architecture, policy consistency, fast-path efficiency, validator correctness, eval validity, provenance, portability, and public-repository accuracy.
- **Likely files:** all changed files; `implementation.md` record.
- **Dependencies:** H1-H6.
- **Tasks:** inspect full Git diff/status/stat; validate all Markdown links; scan secrets/placeholders/caches/temp artifacts/fixture coupling; count entrypoint lines; find duplicated paragraphs/checklists and rules appearing in three or more runtime locations; verify frontmatter against current official docs and provenance against intended repositories.
- **Gate/evidence:** every changed file reviewed, no unintended artifact remains, exact inner tree passes, repository hygiene passes, and every claim is assigned L1-L5 accurately.
- **Failure semantics:** any required blocker remains unchecked and prevents a complete claim; limitations and historical failures remain visible.

### 11.3 Acceptance criteria

- [x] Arbitrary third-party Python imports are rejected by positive stdlib/local-module validation.
- [x] Stdlib and legitimate local imports remain accepted.
- [x] Python support floor is explicit and CI-tested.
- [x] Frontend/browser verification profile exists and remains risk-adaptive.
- [x] Browser tooling is optional and never auto-installed.
- [x] Dependency-change profile exists.
- [x] Performance work follows baseline-hypothesis-change-measure semantics.
- [x] Mid-execution requirement changes preserve unaffected verified work and invalidate only affected evidence.
- [x] Explicit stale/reopened semantics exist.
- [x] Blocking required failures cannot transition to COMPLETE.
- [x] Unrelated/pre-existing failures are classified rather than hidden.
- [x] Required-but-unavailable verification yields NOT_VERIFIED/BLOCKED unless valid alternative evidence exists.
- [x] New adversarial scenarios cover all added profiles.
- [x] Existing five worked examples remain bounded and useful.
- [x] Large-spec example demonstrates requirement change and selective reopening.
- [x] L4 harness runs one scenario per isolated Claude process.
- [x] L4 fixtures are disposable and self-contained.
- [x] L4 captures machine-verifiable evidence where possible.
- [x] Explicit-activation and natural-activation concepts are separated.
- [x] At least the six core L4 scenario families are attempted independently.
- [x] Every L4 scenario has exact PASS/FAIL/BLOCKED/NOT_RUN status.
- [x] Previous blocked L4 history remains preserved.
- [x] Static CI exists for push/PR/manual runs.
- [x] CI requires no secrets.
- [x] CI covers Linux and Windows.
- [x] README uses the real GitHub clone URL.
- [x] README states supported Python version.
- [x] README exposes current CI/evidence status honestly.
- [x] Inner skill-package exact-tree validation remains strict.
- [x] Root-level CI/eval artifacts do not pollute runtime skill.
- [x] All Markdown links resolve.
- [x] No placeholder GitHub username remains.
- [x] No secret material appears in fixtures/reports.
- [x] New policies do not cause trivial tasks to become heavyweight.
- [x] `SKILL.md` remains well below its 200-line ceiling.
- [x] No external integration becomes mandatory.
- [x] Source provenance remains correct.
- [x] L1/L2/L3/L4/L5 claims remain epistemically separate.
- [x] Final report distinguishes architecture quality from observed runtime evidence.

### 11.4 Execution record

| Check | Status | Evidence |
|---|---|---|
| Baseline audit | PASS | Clean `main` worktree at `9909598cc6294b211c3589c68cc0b47117f972b5`; 22 repository files; no `.github` directory or hosted runs observed; all required baseline files read. |
| Positive import validator | PASS | Python 3.14 package validation, 21 tests, and compilation passed. AST classification accepted future/builtin/stdlib/local imports and rejected arbitrary unknown, NumPy, HTTPX, Requests, and Pydantic mutations without importing candidates. |
| Runtime profiles and state semantics | PASS | Stable frontend/browser, dependency, and performance headings; `STALE` selective reopening; user steering; and blocking/optional/unrelated failure semantics passed marker/policy validation and example trace. |
| Expanded L3 evaluation | PASS | Prior 37 scenarios retained; scenarios 38-56 add 19 complete traces across frontend, dependency, performance, requirement-change, and completion families. Repository validator checks row/field coverage. |
| L4 harness and six core runs | PASS | Six explicit-activation families each achieved an independent final PASS in disposable repositories: small, moderate, auth, dirty, missing-graph, formal-spec. Successful-case cost `$0.263199`; all retained attempts `$0.783983`. Natural activation remains NOT RUN. |
| Public repository / CI | PASS | Push/PR/manual workflow authored for Linux/Windows and Python 3.10/3.14; the full CI-equivalent validator/test/compile/hygiene chain passed locally on Python 3.10.20 and 3.14.6. Hosted GitHub Actions remains NOT RUN until a workflow is pushed. |
| Final cross-cutting audit | PASS | Post-record package/repository validators and 21 tests passed; `git diff --check` passed; Markdown/secret/placeholder scans were clean; inner tree remained exactly 17 files; `SKILL.md` was 45 lines; no temp/report artifact entered Git; provenance and optional-integration boundaries remained intact. |

### 11.5 Evidence boundary

- L1/L2: current structural/policy validators, compilation, and 21 mutation tests passed on Python 3.10.20 and 3.14.6.
- L3: the 19 new structured policy traces and retained 37 scenarios were inspected; this is policy coverage, not model behavior.
- L4: all six core explicit-activation fixtures ultimately passed; failed bootstrap and scorer iterations remain in `docs/l4-evaluation.md`.
- L5: NOT RUN; no longitudinal field-effectiveness claim.
- Hosted CI: NOT RUN; local matrix-equivalent evidence does not claim a hosted workflow result.

## 12. Behavioral Calibration and Activation Hardening

This append-only contract governs the post-`ec8b69c` hardening pass. It preserves the established risk-adaptive state machine, progressive-disclosure runtime, exact 17-file inner package, optional-integration boundary, and all historical evidence. It targets five bounded behavioral gaps: natural activation measurement, structurally stable policy validation, a broader evidence-based fast path, a machine-checkable completion contract, and deterministic-enforcement guidance that remains outside the behavioral skill.

### 12.1 Baseline and evidence rules

- Baseline branch/commit: `main` at `ec8b69cf59297e34984eafcfac64e689aa7a6adf`.
- Pre-existing modifications: none; `git status --short` produced no entries.
- Runtime baseline: 17 files; `SKILL.md` 64 lines and 7,130 UTF-8 bytes.
- Historical evidence is retained. New execution records may report `PASS` only after the named command or inspection has actually run.
- L1 structure, L2 policy lint, L3 documented adversarial trace, L4 live Claude behavior, and L5 field evidence remain separate. A lower tier never implies a higher one.
- Skill text is behavioral policy. Hooks and platform controls may enforce deterministically. Observability exposes execution. Codebase-intelligence tools provide optional context. None substitutes for another.

### 12.2 Workstream A — Natural activation reliability and measurement

- **Objective/problem:** measure whether `engineering-core` is selected for natural engineering requests without confusing skill availability, explicit invocation, behavioral resemblance, or optional router guidance with activation.
- **Files:** root `evals/activation/` datasets, harness, tests, and README; `evals/README.md`; `docs/l4-evaluation.md`; root README; `SKILL.md` description only after evidence; repository validator/CI metadata as required. No activation harness enters the runtime package.
- **Tasks:** create positive, negative, and ambiguous prompt datasets spanning implementation, debugging, refactoring, removal, migration, security, billing, release, formal-spec, performance, frontend, generic explanation, and non-engineering writing; support smoke and full profiles; run one isolated repository and Claude process per case; measure explicit and natural modes separately; record Tier A runtime trace, Tier B structured completion output, or Tier C distinctive behavior without inflating weaker evidence; report TP/FP/TN/FN, precision, recall, false-positive rate, false-negative rate, raw counts, time, cost, and limitations; support bounded candidate-description comparisons; retain optional `CLAUDE.md` routing as a separate nonautomatic mechanism.
- **Test/evaluation:** unit-test dataset schema, metric arithmetic, evidence-tier classification, ambiguous-case exclusion, description variants, cost reservation, redaction, and report schema; run a cheap explicit smoke before natural smoke; expand only after smoke validity and budget allow.
- **Gate/evidence:** machine-readable reports distinguish activation from behavior and explicit from natural invocation; final description is justified by observed results or explicitly recorded limitations, not intuition; common positives and clear negatives are both represented.
- **Failure semantics:** unavailable CLI, timeout, budget, permission, malformed stream, or unobservable activation is `BLOCKED`/`NOT_RUN` per case rather than a false pass; ambiguous cases are reported separately; availability in an init event alone is not activation.

### 12.3 Workstream B — Structural policy IDs and validator decoupling

- **Objective/problem:** replace fragile required prose and heading coupling with stable machine-owned policy identifiers while preserving strict tree, frontmatter, link, safety-lint, optionality, import, and line-budget checks.
- **Files:** `engineering-core/SKILL.md`, owning reference files, `engineering-core/scripts/validate_skill.py`, `engineering-core/scripts/test_validate_skill.py`, and validation documentation.
- **Tasks:** place unique lowercase-kebab `<!-- policy-id: ... -->` comments at meaningful policy owners; define required ID-to-file ownership; parse Markdown headings, links, and policy comments with standard-library structural logic; remove exact explanatory-sentence dependencies and description keyword lists; permit editorial heading/prose changes with IDs intact; reject missing, duplicate, malformed, or misplaced required IDs; allow unknown extra IDs; retain narrow forbidden-claim and mandatory-provider safety lint without fuzzy NLP, embeddings, or semantic similarity.
- **Test/evaluation:** mutations must show heading rename with the same ID passes, prose rewrite with the same ID passes, missing ID fails, duplicate ID fails, wrong owner fails, and unknown extra ID passes; all prior import/tree/frontmatter/link/config regressions remain covered.
- **Gate/evidence:** validator behavior is driven by stable structural contracts rather than required natural-language sentences; every required ID has exactly one owner; the real package and mutation suite pass.
- **Failure semantics:** a required ID that is absent, duplicated, malformed, or in the wrong owner is an L1/L2 failure; safety heuristics remain explicitly described as lint, not behavioral proof.

### 12.4 Workstream C — Adaptive Fast-Exit

- **Objective/problem:** broaden the current small-task path beyond typo-sized edits while preventing low line count or file count from downgrading consequential work.
- **Files:** `SKILL.md`, `references/operating-model.md`, `references/repository-investigation.md`, `references/verification-review.md`, relevant examples, and adversarial scenarios.
- **Tasks:** define Low-risk eligibility from evidence, reversibility, precedent, scope clarity, dependency knowledge, verification clarity, and absence of trust/auth/data/billing/concurrency/production/public consequences; include localized bug fixes, null guards, local refactors, renames, clear test corrections, dead helpers, safe config, type fixes, and deterministic rules; use `DISCOVER -> target and nearest context -> internal contract -> implement -> focused verification -> diff -> compact summary`; skip plan artifacts, ledgers, subagents, graph providers, broad scans, full suites, and fresh reviewers by default; impose a context-budget question before another reference or broad file; exit immediately when uncertainty or risk rises.
- **Test/evaluation:** add positive fast-exit traces plus explicit exclusions for one-line authorization/RLS/billing changes, shared dependencies, schema changes, uncertain root cause, unexpected test behavior, and expanding scope; confirm no rule optimizes raw tool-call count.
- **Gate/evidence:** multiple nontrivial but bounded Low-risk examples remain lightweight; consequence-sensitive one-line changes escalate; unexpected evidence returns to normal investigation/planning.
- **Failure semantics:** any failed eligibility condition or emerging uncertainty exits the accelerated path without losing evidence already gathered.

### 12.5 Workstream D — Universal completion-output contract

- **Objective/problem:** make substantive `engineering-core` executions end with a consistent human-readable contract whose claims can be parsed and checked against observed evidence.
- **Files:** `SKILL.md`, `references/verification-review.md`, `references/collaboration-state.md`, examples/scenarios, root completion parser and tests, L4 scorer, and evaluation docs.
- **Tasks:** require the `### Execution Summary` anchor; require `Policy: engineering-core`, Risk, controlled Status, Changed, Verified, and Limitations; use statuses `NO_CHANGE`, `IMPLEMENTED`, `VERIFIED`, `NOT_VERIFIED`, and `BLOCKED`; keep Low summaries compact; allow richer Moderate/High/Critical sections only when relevant; forbid required failures or blockers from coexisting with `VERIFIED`; distinguish model claims from independently observed commands/tests/diffs; implement a standard-library Markdown parser in maintainer tooling, not the runtime package.
- **Test/evaluation:** parser cases cover Low, Moderate, High/Critical, `NO_CHANGE`, `NOT_VERIFIED`, `BLOCKED`, missing policy/status, unknown risk/status, and `VERIFIED` with a blocker; L3 includes a case tempted to claim completion after a required failure; L4 scoring records parsed claims and compares them with independent fixture evidence wherever available.
- **Gate/evidence:** all substantive paths have one stable anchor and controlled status semantics; parser tests pass; required verification failure cannot be reported as verified or complete; optional sections are omitted rather than emitted empty.
- **Failure semantics:** malformed summaries fail completion-contract scoring; claim/evidence mismatch fails or blocks the case according to its cause and remains visible in reports.

### 12.6 Workstream E — Deterministic-enforcement integration guidance

- **Objective/problem:** document how behavioral policy can cooperate with deterministic controls without shipping a runnable guard, claiming impossibility, or conflating hooks, observability, and context providers.
- **Files:** root `docs/deterministic-enforcement.md`, root README, `engineering-core/references/integrations.md`, `SKILL.md` summary, and one adversarial scenario.
- **Tasks:** compare Claude permissions, sandbox/managed policy, `PreToolUse`, Safety Net/DCG-style controls, and organization controls; cover Git reset/clean/force/history, destructive filesystem operations and wildcards, database drop/truncate, production deploy, credentials, and provider-side effects; warn that naive substring matching misses wrappers, PowerShell, Python, `xargs`/`find`, encoded payloads, SQL inside scripts, and indirect execution while also causing false positives; specify allow/deny/ask, timeout, crash, parse, unsupported-platform, logging, and secret-redaction design considerations; provide test-fixture categories rather than runnable guard code.
- **Test/evaluation:** inspect that no executable hook/config is added, optionality remains explicit, responsibility boundaries are consistent, and the L3 scenario routes a deterministic-control need to external enforcement without weakening skill policy.
- **Gate/evidence:** guidance is linked from README/runtime integration summary, remains platform-aware and non-prescriptive about universal fail-open/fail-closed behavior, and leaves project owners in control of installation.
- **Failure semantics:** absent enforcement remains a disclosed limitation, not a skill guarantee; unsupported or failed controls require the deployment's documented fallback/escalation behavior.

### 12.7 Dependency order and release gates

1. Freeze baseline and append this contract.
2. Build activation datasets/harness/tests before optimizing the description.
3. Replace prose-coupled validation with structural policy IDs and mutation tests.
4. Refine Adaptive Fast-Exit policy and its escalation scenarios.
5. Add the completion-output contract, parser, and claim-versus-evidence scoring.
6. Add deterministic-enforcement guidance and responsibility-boundary audit.
7. Expand L3 traces while retaining every historical scenario and failure.
8. Run L1/L2/unit/compile/repository validation, then bounded L4 explicit and natural smoke evaluations.
9. Perform diff-first, exact-tree, line-budget, link, secret, active-config, duplication, provenance, and evidence-level audits.
10. Check acceptance items only when the execution record names concrete supporting evidence; commit, push `main`, and verify local/remote SHA equality only after all release blockers are resolved.

Release is blocked by any failed required validation, exact-tree pollution, missing required policy ID, completion-contract contradiction, fabricated activation claim, secret/config artifact, unresolved critical review finding, or local/remote SHA mismatch. Live activation limitations may remain `BLOCKED` or `NOT_RUN` only when reported honestly and when the implementation and static/unit gates themselves pass.

### 12.8 Acceptance criteria

- [x] Natural activation infrastructure lives outside the runtime package.
- [x] Positive, negative, and ambiguous activation datasets exist.
- [x] Explicit and natural activation are measured separately.
- [x] Activation reports include TP, FP, TN, FN, precision, recall, false-positive rate, and false-negative rate wherever live evidence permits.
- [x] The skill description is evaluated rather than accepted by intuition.
- [x] Activation tuning does not overfit a tiny prompt set.
- [x] Core capability presence no longer depends on exact prose strings.
- [x] Stable policy IDs define machine-owned capability anchors.
- [x] Editorial heading and prose changes pass when the owning policy ID remains intact.
- [x] Missing, duplicate, and misplaced required policy IDs fail validation.
- [x] Validator logic uses no fuzzy NLP, embeddings, or semantic-similarity dependency.
- [x] Adaptive Fast-Exit covers bounded Low-risk work beyond typo-sized edits.
- [x] Fast-Exit eligibility depends on evidence and risk, not line or file count.
- [x] One-line authorization, RLS, and billing changes are excluded from Fast-Exit.
- [x] Fast-Exit ends immediately when uncertainty or consequence rises.
- [x] Low-risk accelerated work avoids plans, agents, maps, broad suites, and broad scans by default.
- [x] Substantive executions use the `### Execution Summary` anchor.
- [x] Completion reports include Policy, Risk, Status, verification, and limitations.
- [x] Low-risk completion output remains compact.
- [x] Moderate/High/Critical output may be richer without empty boilerplate sections.
- [x] Completion uses only the controlled status vocabulary.
- [x] A required failure prevents `VERIFIED` or complete-equivalent reporting.
- [x] Model completion claims are distinguished from independently observed evidence.
- [x] Completion parsing and tests exist wherever evaluation relies on the contract.
- [x] Deterministic-enforcement integration guidance exists outside the runtime package.
- [x] Skill, hooks/control plane, observability, and codebase-intelligence boundaries remain explicit.
- [x] No runnable destructive-command guard or hook configuration ships in the skill.
- [x] Guidance warns about naive command matching, wrappers, indirect execution, false positives, and false negatives.
- [x] Optional router guidance remains nonautomatic and non-deterministic.
- [x] `SKILL.md` remains below 200 lines.
- [x] Exact runtime-tree validation remains strict.
- [x] L1/L2/L3/L4/L5 evidence levels remain distinct.

### 12.9 Execution record

| Check | Status | Evidence |
|---|---|---|
| Baseline audit | PASS | Clean `main` worktree at `ec8b69cf59297e34984eafcfac64e689aa7a6adf`; 17-file runtime package; `SKILL.md` 64 lines / 7,130 UTF-8 bytes; origin points to `aydinogluomer-sys/engineering-core`. |
| Activation infrastructure and calibration | PASS | Maintainer-only harness tests passed 10/10. Corrected explicit case was TP=1; natural candidate comparison improved smoke recall from 0.25 to 0.50 with precision 1.00. Candidate 1 full set retained precision 1.00 / recall 0.50 across 12 positive and 8 negative prompts; four ambiguous prompts were separate. Costs and invalid calibration attempts are retained in `docs/l4-evaluation.md`. |
| Structural policy-ID validator | PASS | Structural/Policy-Lint validation passed and 24/24 mutation tests passed, including heading/prose edits, missing/duplicate/misplaced IDs, unknown extension IDs, malformed IDs, exact tree, imports, links, frontmatter, and safety lint. The first post-change run's obsolete provenance-string test failed and was retained in execution output before replacement with the no-fuzzy-semantics regression. |
| Adaptive Fast-Exit | PASS | Runtime entrypoint defines evidence/risk eligibility, expanded examples, default ceremony exclusions, context question, and immediate exits. L3 scenarios 57-61 trace local null guard/rename, unexpected failure, one-line RLS, and dependency expansion. |
| Completion-output contract | PASS | Standard-library parser passed 14/14 tests; L4 event scorer passed 4/4. After retained behavior/scorer refinements, explicit Small and High/auth fixtures both achieved machine-scored PASS with independent tests/diffs and parsed six-field summaries. |
| Deterministic-enforcement guidance | PASS | Root guidance covers permissions, sandbox, managed policy, `PreToolUse`, Safety Net/DCG patterns, action families, indirect execution, FP/FN, timeout/crash/parse/platform behavior, logging/redaction, and fixtures. Audit found zero active hook/config artifacts in the 17-file runtime package. |
| L3 adversarial evaluation | PASS | Historical scenarios 1-56 remain; scenarios 57-77 add five Fast-Exit, five activation, six completion, four validator, and one deterministic-enforcement trace, each with owning policy, observed result, and L3 label. |
| Final pre-publication audit | PASS | Python 3.14.6 validation: inner validator, 24 mutation tests, 14 parser tests, 4 scorer tests, 10 activation tests, repository validation, compilation, skill-creator validation, and `git diff --check` passed. Runtime remained exactly 17 files; `SKILL.md` was 68 lines; secret, active-config, and tracked-report scans were clean. Python 3.10 was unavailable locally; static CI retains 3.10/3.14 on Linux/Windows. |
| Repository publication | PASS | Evidence commit `6ddfb42d8ee10e0d8f244caecf21ae0c177790e6` was pushed to `origin/main`; `git rev-parse HEAD` and `git ls-remote origin refs/heads/main` returned the same SHA. This publication record is committed separately so it does not claim success before the push occurred. |

### 12.10 Evidence boundary

- **L1:** PASS for exact tree, frontmatter, links, syntax/imports, policy-ID structure, line budget, and absence of active runtime integration artifacts.
- **L2:** PASS for narrow forbidden guarantees/provider-mandatory lint and the documented layer boundaries; this is not proof of model behavior or security.
- **L3:** PASS for retained scenarios 1-77, including the 21 new structured traces.
- **L4:** PASS for bounded explicit Small/auth completion cases and bounded explicit/natural activation samples. Natural candidate-1 full-set recall was 0.50, so natural activation reliability is measured but incomplete—not guaranteed.
- **L5:** NOT RUN; no longitudinal field population was evaluated.
