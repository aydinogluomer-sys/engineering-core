# Repository Investigation

Read this reference for unfamiliar repositories, instruction discovery, evidence acquisition, bounded context, impact tracing, and optional code-intelligence providers.

## 1. Discover instructions before edits

Look for instructions applicable to the target surface, including:

- platform/managed constraints;
- explicit user constraints;
- root and nested `CLAUDE.md` / `CLAUDE.local.md`;
- `.claude/rules`;
- `AGENTS.md`;
- contribution guides;
- package/module documentation;
- architecture or implementation specifications;
- build/test/type/lint configuration;
- relevant specialist skill descriptions.

Resolve conflicts by authority, scope, and specificity:

1. platform/managed safety and permissions;
2. explicit user objective, constraints, and authorization;
3. repository instructions applicable to the target path;
4. specialist skill mechanics for the domain;
5. `engineering-core` defaults;
6. optional tool suggestions.

Do not pretend concatenated instructions technically “override” each other when the runtime simply loads them together. Identify material conflicts and resolve by scope/specificity; escalate consequential ambiguity.

## 2. Evidence hierarchy

Prefer current repository and runtime evidence over memory or summaries.

Useful evidence, depending on the task:

- source code;
- tests;
- schemas/migrations;
- configuration;
- generated artifacts plus their source generator;
- package manifests/lockfiles;
- Git status and diff;
- recent relevant history;
- type/language tooling;
- runtime behavior/logs;
- current authoritative specification.

Treat memory, old conversation summaries, code maps, graph indexes, comments, READMEs, and agent summaries as leads until consequential claims are grounded in current evidence.

Do not assume existing code is correct merely because it exists.

## 3. Start cheap and bounded

Begin with the smallest useful evidence set:

- worktree status;
- relevant instruction files;
- target symbol/file;
- nearest tests;
- nearest established precedent;
- direct callers/consumers;
- directly relevant manifest/config/schema.

Expand only to answer an unanswered question that affects:

- implementation design;
- blast radius;
- safety;
- compatibility;
- verification.

Stop gathering context when the change contract, likely impact, and verification strategy are supported.

Do not read the entire repository by default.

## 4. Evidence ledger for non-trivial work

Track, internally or in an approved task/state system:

| Field | Purpose |
|---|---|
| Requirement / hypothesis | What must be true or what is being tested |
| Evidence | Source/test/config/runtime observation |
| Confidence / open question | What remains uncertain |
| Affected surface | Files/interfaces/data/state |
| Planned proof | How correctness will be checked |

Use the ledger to prevent repeated searches and unsupported assertions.

## 5. Impact tracing

For cross-file behavior, inspect enough of the chain to understand:

- definition;
- callers/consumers;
- shared interfaces/types;
- data flow;
- persistence or external side effects;
- tests that encode the contract.

For refactors or removals, also inspect:

- imports/exports;
- registration points;
- routes;
- feature flags;
- configuration/env;
- generated references;
- build/CI references.

## 6. Optional codebase-intelligence providers

CodeGraph, Cartographer, Graphify, language servers, repository indexes, and similar systems are optional context providers.

Before relying on consequential output, consider:

- provider availability;
- repository identity;
- index freshness;
- source location/provenance;
- whether relevant languages/artifact types are covered.

Use provider output to locate and structure evidence.

For consequential conclusions, verify against current source/config/tests/runtime behavior.

Avoid both extremes:

- blindly trusting a stale graph;
- ignoring a precise fresh graph and re-reading the whole repository.

## 7. Native fallback

If an optional provider is absent, stale, incompatible, or fails:

- continue with native repository search/read tools;
- use language tooling already present;
- use Git status/diff/history;
- use targeted test discovery.

Absence of a graph provider is not a blocker.

Never install a provider solely because this skill mentions it.

## 8. Generated artifacts

Recognize generated code/types/config.

When a source generator exists:

1. find the source of truth;
2. modify the source;
3. regenerate using repository tooling;
4. inspect the generated diff.

Do not manually patch generated output unless the repository explicitly treats it as authoritative.

## 9. Context-stop rule

Before reading another broad surface, ask:

“What decision will this evidence change?”

If there is no concrete decision, risk question, or verification gap, stop expanding context.
