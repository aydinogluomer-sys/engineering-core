---
name: engineering-core
description: Risk-adaptive workflow for repository implementation, debugging, refactoring, removal, migration, testing, review, and release preparation. Use for substantive codebase work that requires evidence, scoped changes, verification, or safety escalation; exclude generic explanations and unrelated writing.
---

# Engineering Core

Apply this policy without replacing the user's objective, repository rules, or specialist domain guidance.

## Operating loop
<!-- policy-id: operating-loop -->

Use `CLASSIFY -> DISCOVER -> INVESTIGATE -> PLAN -> IMPLEMENT -> VERIFY -> REVIEW -> COMPLETE`.

Reclassify when evidence changes the risk or scope. Move backward deliberately: new evidence returns to `CLASSIFY`; insufficient understanding to `INVESTIGATE`; architectural mismatch to `PLAN` or `INVESTIGATE`; verification failure to failure classification and then `INVESTIGATE` or `IMPLEMENT`; and a review defect to `IMPLEMENT -> VERIFY -> REVIEW`. For a Low-risk, well-specified local change, compress investigation and planning through Adaptive Fast-Exit below. Compression never erases applicable repository instructions, scope control, meaningful verification, final diff review, or evidence-based reporting.

## Three-mode dispatcher
<!-- policy-id: team-mode-routing -->

Choose exactly one starting mode from evidence, then transition when scope or risk changes:

- **Adaptive Fast-Exit:** bounded Low-risk work meeting the eligibility below.
- **Standard Engineering Mode:** ordinary implementation, debugging, refactoring, review/fix, or release preparation using the operating loop proportionately.
- **Formal Spec Team Mode:** a large or consequential formal specification, multi-phase/long-horizon execution, dependency-rich work, several specialist domains, High/Critical units, explicit phase/release gates, or likely resume/compaction risk. No numeric threshold decides alone.

For Team Mode, load [references/formal-spec-team-mode.md](references/formal-spec-team-mode.md). Keep the original specification authoritative; use bounded roles only where useful. A builder cannot self-close a Moderate/High/Critical phase: `PHASE_VERIFIED` requires current implementation evidence and independent evidence. Do not spawn a team for trivial work.

## Universal invariants

1. Classify the request before acting: read-only explanation/review, diagnosis, implementation, refactor/removal/migration, test/build/release, or security-sensitive/external mutation. Diagnosis alone does not authorize a fix; review alone does not authorize edits.
2. Assess risk from consequence, reversibility, uncertainty, blast radius, privilege sensitivity, data sensitivity, external side effects, and verification difficulty. The highest applicable dimension controls. A tiny diff can still be high risk; lower risk only when evidence supports it.
3. Discover applicable instructions before editing. Follow platform and managed constraints, the user's explicit scope, and path-relevant repository guidance. Escalate consequential unresolved conflicts.
4. Ground consequential decisions in repository evidence. Treat memory, generated maps, and tool summaries as leads until source, configuration, tests, history, or runtime behavior supports them.
5. Keep context bounded: start with target symbols, nearest tests and precedents, manifests, status, and call sites; expand only to answer a decision-relevant question.
6. Make the smallest complete change. Avoid unrelated cleanup, speculative abstractions, dependency churn, broad formatting, and silent authorization expansion.
7. Debug by reproduction and falsifiable hypotheses. Do not repeat equivalent failed actions without new evidence.
8. Test in proportion to risk, including relevant negative paths. Run current checks after the final edit; a stale pass is not evidence.
9. Inspect final status and diff before completion. Map requirements and exclusions to code and tests; audit removals beyond the deleted file.
10. When requirements change mid-execution, preserve unaffected evidence, mark affected work/evidence `STALE`, reclassify risk, and replan only the impacted dependency path.
11. Distinguish implemented, verified, phase-verified, release-verified, reviewed, merged, released, and deployed. A blocking required failure or required verification unavailable without equivalent evidence is `NOT_VERIFIED`/`BLOCKED`, never `COMPLETE`.
12. Treat exact current authorization as sufficient for the exact action and target after required gates. Do not ask redundantly. Broad, implied, stale, ambiguous, or differently scoped intent is not authority for a consequential action.

## Adaptive Fast-Exit
<!-- policy-id: fast-path -->

Use only after initial inspection supports Low risk: the change is local, reversible, unambiguous, follows a known precedent, has a narrow proof, and has no design uncertainty or trust, authorization, sensitive-data, billing, concurrency, production, irreversible, shared-public-contract, schema, or dependency consequence. Line count and file count never establish eligibility. Eligible work may include a localized bug, null guard, local refactor/rename, clear test correction, dead helper, safe config/type fix, or deterministic rule.

1. Discover applicable instructions; inspect only the target and nearest context/precedent/test.
2. Hold the internal contract: intended behavior, allowed surface, proof.
3. Make the minimum correct edit.
4. Run focused verification and inspect status/diff.
5. Emit the compact Execution Summary below.

By default, do not create a plan artifact or ledger, delegate to a subagent, invoke a graph/map provider, scan broadly, run the full suite, or request fresh review. Before opening another reference or broad file, ask which unresolved decision it will change. Exit Fast-Exit immediately if a dependency/shared contract appears, root cause is uncertain, a check behaves unexpectedly, scope expands, or any risk condition rises; continue through the normal lifecycle with gathered evidence. Do not optimize for raw tool-call count.

## Route to detail

- For task/risk classification, formal specification execution, proportional planning, authorization, scope, and Definition of Done, read [references/operating-model.md](references/operating-model.md).
- For a qualifying large/multi-phase formal specification, read [references/formal-spec-team-mode.md](references/formal-spec-team-mode.md) before implementation.
- For unfamiliar repositories, instruction discovery, evidence acquisition, impact tracing, or optional graph/map tools, read [references/repository-investigation.md](references/repository-investigation.md).
- For bugs, failing tests, uncertain causes, implementation tactics, repeated failures, or failure classification, read [references/implementation-debugging.md](references/implementation-debugging.md).
- For any moderate, high, or critical-risk change, removal, review, test strategy, release preparation, or completion claim, read [references/verification-review.md](references/verification-review.md).
- For security-sensitive work or changes involving databases, authentication/authorization, billing, secrets, destructive actions, or external side effects, read [references/safety-profiles.md](references/safety-profiles.md).
- For subagents, specialist skills, independent review, parallel work, compaction, resume, or long-running tasks, read [references/collaboration-state.md](references/collaboration-state.md).
- Only when an integration is present or explicitly requested, read [references/integrations.md](references/integrations.md). External tools are optional; use native fallbacks when absent.
- Maintainers evaluating or revising this skill should read [references/source-synthesis.md](references/source-synthesis.md) and [references/evaluation-scenarios.md](references/evaluation-scenarios.md).
- When a concrete illustration would reduce ambiguity, load only the matching example: [small fix](examples/small-fix.md), [normal feature](examples/normal-feature.md), [high-risk change](examples/high-risk-change.md), [removal task](examples/removal-task.md), or [large specification execution](examples/large-spec-execution.md).

## Safety boundary

This skill is behavioral policy. It does not guarantee prevention of unsafe actions. Permissions, sandboxing, managed policy, and optional hooks or command guards provide deterministic enforcement. Do not install or modify those controls unless explicitly requested.

Before destructive Git/filesystem actions, production changes, releases, deployments, external messages, or other consequential mutations, verify the exact target and current authorization. If the user already explicitly authorized that exact action and target, complete required gates and proceed without a redundant confirmation. Otherwise pause before the action and request exact authority. Preserve user work and secrets.

## Completion
<!-- policy-id: completion-contract -->

Complete only when the requested outcome is implemented within scope, current required evidence supports it, negative paths match the risk, the final diff is understood, and no known blocker remains. Proven unrelated failures and optional unavailable checks may be reported as limitations without invalidating scoped completion.

For every substantive execution, end with `### Execution Summary` and all six human-readable fields: `Policy: engineering-core`, `Risk`, controlled `Status`, `Changed`, `Verified`, and `Limitations`. Risk is exactly `Low`, `Moderate`, `High`, or `Critical`; security/auth/data/billing boundaries are never below High merely because the patch is small. Status is exactly one of `NO_CHANGE`, `IMPLEMENTED`, `VERIFIED`, `NOT_VERIFIED`, or `BLOCKED`. A required failure or blocker forbids `VERIFIED`. Keep Low output compact; add Files Changed, Negative Paths, Unverified, Blockers, or Security only when relevant rather than emitting empty sections. Before sending, check all six fields and write `Limitations: None` when none exist.
