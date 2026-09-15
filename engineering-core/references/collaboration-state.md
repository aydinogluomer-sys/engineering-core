# Collaboration and State

Read this reference for subagents, specialist skills, parallel work, independent review, long-running tasks, compaction, resume, and handoffs.

## 1. Delegate only bounded work

Subagents are an optimization, not a ritual.

Good delegation candidates:

- read-only repository research;
- independent module analysis;
- specialist security review;
- test-gap analysis;
- documentation/reference lookup;
- fresh review;
- isolated implementation in non-overlapping worktrees/files.

Avoid multiple agents editing overlapping files without explicit ownership or worktree isolation.

## 2. Delegation contract

Every delegated task should define:

- objective;
- allowed scope/files;
- read-only versus write authority;
- expected deliverable;
- required evidence;
- stop condition;
- what not to modify.

Do not trust a “done” message without inspecting the actual artifacts/evidence.

## 3. Builder + reviewer

For Moderate, High, or Critical work, a strong pattern is:

`builder -> independent reviewer -> fix -> verify`

The reviewer should be unprimed by the builder's conclusions and receive the actual request, relevant instructions, diff, and evidence.

Do not require a second agent for trivial Low-risk work.

## 4. Specialist routing

`engineering-core` owns cross-cutting process:

- evidence;
- risk;
- scope;
- safety boundaries;
- coordination;
- verification;
- completion semantics.

A specialist owns domain mechanics.

Examples:

- Trail-of-Bits-style specialist -> deep AppSec;
- Terraform specialist -> Terraform mechanics;
- Android RE skill -> APK/bytecode analysis;
- design specialist -> visual/art-direction mechanics;
- research specialist -> AI/ML research workflow.

Do not duplicate specialist knowledge in the core.

## 5. Conflict resolution

Use authority and specificity:

1. platform/managed safety/permissions;
2. explicit user objective/constraints;
3. path-relevant repository instructions;
4. relevant specialist mechanics;
5. engineering-core defaults;
6. optional tool suggestions.

The specialist may override generic implementation mechanics in its domain, while the core retains cross-cutting evidence, authorization, user-work safety, verification, and completion requirements.

Escalate consequential unresolved conflict.

## 6. Long-horizon state

For work likely to span context compaction, sessions, or many gates, maintain compact state using an existing task system or a user/repository-approved file.

Do not create repository artifacts by default.

Record only what is needed to continue reliably:

- objective;
- current authorization boundary;
- decisions;
- important evidence/invariants;
- modified files;
- commands/results;
- open failures/blockers;
- current work unit;
- next action;
- stop conditions.

Avoid unbounded chronological logs.

## 7. Resume protocol

On resume:

1. read the compact state;
2. verify repository identity and worktree status;
3. verify that key files/state still match;
4. treat old test passes as stale after relevant edits;
5. reclassify risk if scope/state changed;
6. continue from the latest supported state.

Never assume a state record is current merely because it exists.

## 8. Compaction resilience

Universal invariants belong in the lean `SKILL.md`.

Detailed policy belongs in references.

Before compaction or a major session transition, preserve only continuation-critical state. Do not duplicate full reference content into notes.

## 9. Handoff evidence

A useful handoff contains:

- exact task/work unit;
- scope;
- current status;
- evidence already observed;
- unresolved questions;
- checks still required.

A handoff must not turn inference into fact.
