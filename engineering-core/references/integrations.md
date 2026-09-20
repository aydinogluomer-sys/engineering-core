# Optional Integrations

Read this reference only when an integration is present, requested, or materially useful.

External integrations are optional. The base skill must work without them.

## 1. Four-layer separation
<!-- policy-id: optional-integrations -->

| Layer | Responsibility |
|---|---|
| Engineering skill | Behavioral workflow/policy |
| Hooks / control plane | Deterministic allow/deny/ask/enforcement |
| Observability | Execution visibility and telemetry |
| Codebase intelligence | Context discovery and relationship mapping |

Do not conflate these responsibilities.

## 2. Codebase intelligence

Potential providers include CodeGraph, Cartographer, Graphify, language servers, and repository indexes.

Before relying on a provider, check when practical:

- it is available;
- it points to the intended repository;
- its index/artifacts are fresh enough;
- results expose source location/provenance;
- relevant languages/artifacts are covered.

Use provider output to find/structure evidence.

For consequential conclusions:

`provider result -> current source/config/test verification`

### Provider strengths

- CodeGraph-like systems: symbols, callers/callees, cross-file dependencies, blast radius.
- Cartographer-like systems: bounded implementation briefs, graph freshness, removal/completeness audits, evidence-backed notes.
- Graphify-like systems: code plus docs/schema/media semantic relationships and provenance labels.

Do not hard-depend on any provider.

## 3. Native fallback

If a provider is unavailable, stale, fails, or lacks coverage:

- use repository search/read tools;
- language tooling already present;
- Git;
- targeted tests.

Do not install a provider solely because the skill mentions it.

## 4. Hooks / deterministic enforcement
<!-- policy-id: deterministic-enforcement -->

Hooks may enforce policies that prompt text cannot guarantee, such as:

- blocking destructive shell/Git commands;
- protecting secret files;
- auditing permissions;
- validating selected lifecycle events;
- capturing session/subagent state.

Design hooks with explicit event scope, allow/deny/ask semantics, timeout/failure behavior, and test fixtures.

Command-string matching alone is fragile: wrappers, shell aliases, PowerShell, interpreter calls, pipelines, encoded payloads, SQL inside scripts, and indirect provider actions can evade naive patterns, while broad substrings can block benign work. Threat-model false positives and false negatives, supported platforms, parse errors, crashes, timeout posture, audit logging, and secret redaction. There is no universal fail-open/fail-closed choice; select it by consequence.

Do not install/enable hooks without explicit user intent.

The public repository's maintainer guidance in `docs/deterministic-enforcement.md` expands this boundary without shipping executable hook configuration in the runtime skill.

## 5. Observability

Observability may track:

- session lifecycle;
- subagent start/stop;
- tool calls/failures;
- permission requests;
- handoffs;
- validation events;
- context compaction;
- resource/token usage.

Observability does not prove correctness.

Redact secrets and sensitive payloads.

Do not turn missing telemetry into a release blocker unless repository policy explicitly requires it.

## 6. Optional CLAUDE.md routing
<!-- policy-id: activation-guidance -->

Skill activation is model-driven and should not be treated as deterministic.

Users who want stronger project-level guidance may optionally add a routing rule to their own `CLAUDE.md`, for example:

> For substantive software-engineering implementation, debugging, refactoring, migration, review, or release work, apply the engineering-core skill unless a more specific applicable instruction supersedes its workflow mechanics.

This is optional integration guidance.

The skill must not modify `CLAUDE.md` automatically.

A `CLAUDE.md` router is stronger repository/user-level guidance, but still not a deterministic enforcement mechanism.

See the repository-level `docs/claude-router.md` when distributed from the public repository.

## 7. Integration trust

Treat integrations as independently trusted dependencies.

Do not grant broader permissions, install packages, or change configuration merely to make an optional integration work without user intent.
