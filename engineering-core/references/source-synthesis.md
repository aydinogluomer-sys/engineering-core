# Source Synthesis

Maintainer reference only. Do not load during ordinary engineering work.

`engineering-core` synthesizes principles from existing systems; it does not concatenate or replace them.

| Source | Observed principle | Decision | Implementation location | Rationale |
|---|---|---|---|---|
| Official Claude Code docs | Skills should be focused, progressively disclosed, and triggered by clear descriptions; repository instructions and context discipline matter | Adopted | `SKILL.md`, all references | Runtime-target source of truth |
| Superpowers (`obra/superpowers`) | Separate understanding/planning/implementation/verification; root-cause debugging; fresh review | Adopted, made risk-adaptive | `operating-model.md`, `implementation-debugging.md`, `verification-review.md` | Strong engineering discipline without forcing ceremony on tiny tasks |
| gstack (`garrytan/gstack`) | Think/plan/build/review/test/ship lifecycle; product/engineering intent; release gates | Modified | `operating-model.md`, `verification-review.md` | Retains lifecycle/release rigor without importing the full opinionated operating system |
| Trail of Bits skills (`trailofbits/skills`) | Audit context, differential review, sharp edges, variant analysis, post-patch validation | Adopted selectively | `safety-profiles.md`, `verification-review.md` | Deep security is risk-triggered; specialist remains better for full AppSec audits |
| Safety Net / DCG | Prompt guidance cannot deterministically block destructive commands | Adopted | `SKILL.md` safety boundary, `safety-profiles.md`, `integrations.md` | Separates behavioral policy from runtime enforcement |
| Hooks Mastery (`disler/claude-code-hooks-mastery`) | Lifecycle hooks are a deterministic control plane with explicit semantics | Adopted conceptually | `integrations.md` | Core documents integration but does not install hooks |
| Multi-Agent Observability (`disler/claude-code-hooks-multi-agent-observability`) | Agent/tool/handoff telemetry improves traceability but is not correctness | Adopted | `integrations.md`, `collaboration-state.md` | Preserves visibility/correctness distinction |
| CodeGraph (`colbymchenry/codegraph`) | Semantic symbol/call/dependency graph and blast-radius context for coding agents | Adopted as optional provider pattern | `repository-investigation.md`, `integrations.md` | Useful context acceleration; source verification remains authoritative |
| Cartographer (`kingbootoshi/cartographer`) | Bounded briefs, graph freshness, removal/completeness audits, evidence-backed notes | Adopted selectively | `repository-investigation.md`, `verification-review.md`, `integrations.md` | Strong task-oriented repository intelligence without hard dependency |
| Graphify (`Graphify-Labs/graphify`) | Relationship graph spanning code/docs and provenance for extracted/inferred edges | Adopted as optional broad-context provider | `repository-investigation.md`, `integrations.md` | Complements pure code graphs; not required |
| ClaudeKit (`mrgoonie/claudekit-skills`) | Systematic debugging, root-cause tracing, verification-before-completion, specialist routing | Adopted selectively | `implementation-debugging.md`, `verification-review.md`, `collaboration-state.md` | Useful patterns without importing broad library scope |
| Alireza Claude Skills (`alirezarezvani/claude-skills`) | Modular specialist skills and broad skill discoverability | Adopted structurally | `SKILL.md`, `collaboration-state.md` | Keeps core narrow and specialists modular |

## Intentionally rejected

- Mandatory heavyweight planning for every task.
- Mandatory multi-agent execution.
- Mandatory TDD regardless of task type.
- Mandatory graph/index tooling.
- Automatic hook or MCP installation.
- Treating observability as proof of correctness.
- Reimplementing specialist domains inside the core.
- A monolithic `SKILL.md`.
- Static validator claims about runtime model behavior.

## Core differentiator

The core is the integration of:

`risk-adaptive workflow + evidence-first context + minimum-correct implementation + systematic debugging + targeted verification + security escalation + fresh review + safe delegation + honest completion`

Its goal is not to beat each specialist at its specialty. Its goal is to provide a coherent cross-cutting engineering control policy.
