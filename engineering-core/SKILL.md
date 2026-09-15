---
name: engineering-core
description: Core operating policy for software-engineering work across repositories. Use when implementing, debugging, refactoring, removing, reviewing, testing, migrating, or preparing code for release; scale investigation, planning, safety, and verification to the task's actual risk.
---

# Engineering Core

Apply this policy without replacing the user's objective, repository rules, or specialist domain guidance.

## Operating loop

Use `CLASSIFY -> DISCOVER -> INVESTIGATE -> PLAN -> IMPLEMENT -> VERIFY -> REVIEW -> COMPLETE`.

Reclassify when evidence changes the risk or scope. Move backward deliberately: new evidence returns to `CLASSIFY`; insufficient understanding to `INVESTIGATE`; architectural mismatch to `PLAN` or `INVESTIGATE`; verification failure to failure classification and then `INVESTIGATE` or `IMPLEMENT`; and a review defect to `IMPLEMENT -> VERIFY -> REVIEW`. For a low-risk, well-specified local change, compress investigation and planning through the fast path below. Compression never erases applicable repository instructions, scope control, meaningful verification, final diff review, or evidence-based reporting.

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
10. Distinguish implemented, verified, phase-verified, release-verified, reviewed, merged, released, and deployed. Claim only the states supported by current observed evidence; an unmet Definition of Done cannot transition to `COMPLETE`.
11. Treat exact current authorization as sufficient for the exact action and target after required gates. Do not ask redundantly. Broad, implied, stale, ambiguous, or differently scoped intent is not authority for a consequential action.

## Small-task fast path

For a clear, localized, reversible, low-risk task:

1. Read applicable instructions and inspect the target plus nearest precedent/test.
2. Hold a one-sentence change contract: intended behavior, allowed surface, proof.
3. Make the minimum edit.
4. Run the narrowest meaningful check and inspect the diff.
5. Report the result, evidence, and any unverified limitation.

Do not create a design document, repository-wide map, subagent workflow, or full-suite run unless repository policy or discovered risk requires it.

## Route to detail

- For task/risk classification, formal specification execution, proportional planning, authorization, scope, and Definition of Done, read [references/operating-model.md](references/operating-model.md).
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

Complete only when the requested outcome is implemented within scope, current relevant checks have passed or their failures are accurately reported, negative paths match the risk, the final diff is understood, and no known blocker is hidden.
