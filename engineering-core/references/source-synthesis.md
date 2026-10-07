# Source Synthesis

Maintainer reference only. Do not load during ordinary engineering work.

Provenance was refreshed on 2026-10-04. GitHub commit values below are observed remote `HEAD` snapshots, not vendored dependencies or immutable claims about earlier design work. Sources not independently resolved remain explicitly `UNVERIFIED` rather than receiving an invented commit.

`engineering-core` synthesizes principles from existing systems; it does not concatenate or replace them.

| Source | Observed principle | Decision | Implementation location | Rationale |
|---|---|---|---|---|
| [Official Claude Code docs](https://code.claude.com/docs/en/features-overview), inspected 2026-10-04 | Skills are on-demand behavioral knowledge; hooks are deterministic lifecycle enforcement; repository instructions and isolated subagents have distinct roles | Adopted | `SKILL.md`, all references | Runtime-target source of truth |
| [Superpowers](https://github.com/obra/superpowers), `8ca22dba9a94f28898bbce59f2537ff4d87c747d` | Separate understanding/planning/implementation/verification; root-cause debugging; fresh review | Adopted, made risk-adaptive | `operating-model.md`, `implementation-debugging.md`, `verification-review.md` | Strong engineering discipline without forcing ceremony on tiny tasks |
| [gstack](https://github.com/garrytan/gstack), `2db0b3adc84b95be08d08bda4f9799ca7fa8665e` | Think/plan/build/review/test/ship lifecycle; product/engineering intent; release gates | Modified | `operating-model.md`, `verification-review.md` | Retains lifecycle/release rigor without importing the full opinionated operating system |
| [Trail of Bits skills](https://github.com/trailofbits/skills), `82fe8226252622fa807643bdca1710901198553a` | Audit context, differential review, sharp edges, variant analysis, post-patch validation | Adopted selectively | `safety-profiles.md`, `verification-review.md` | Deep security is risk-triggered; specialist remains better for full AppSec audits |
| Safety Net / DCG, upstream identity `UNVERIFIED` | Prompt guidance cannot deterministically block destructive commands | Adopted | `SKILL.md` safety boundary, `safety-profiles.md`, `integrations.md` | No source URL/commit is asserted until independently resolved |
| [Hooks Mastery](https://github.com/disler/claude-code-hooks-mastery), `052ad1cbd5aeb1ec4a1def22012d1293c6225625` | Lifecycle hooks are a deterministic control plane with explicit semantics | Adopted conceptually | `integrations.md` | Core documents integration but does not install hooks |
| [Multi-Agent Observability](https://github.com/disler/claude-code-hooks-multi-agent-observability), `8a6e5cf795df50767cea7123703751282a819697` | Agent/tool/handoff telemetry improves traceability but is not correctness | Adopted | `integrations.md`, `collaboration-state.md` | Preserves visibility/correctness distinction |
| [CodeGraph](https://github.com/colbymchenry/codegraph), `6560052a6f856855d3f71eee838fd66ccfa4285d` | Semantic symbol/call/dependency graph and blast-radius context for coding agents | Adopted as optional provider pattern | `repository-investigation.md`, `integrations.md` | Useful context acceleration; source verification remains authoritative |
| [Cartographer](https://github.com/kingbootoshi/cartographer), `a62d16981b6aa1f5f6ef56701c49b81a16a8e30a` | Bounded briefs, graph freshness, removal/completeness audits, evidence-backed notes | Adopted selectively | `repository-investigation.md`, `verification-review.md`, `integrations.md` | Strong task-oriented repository intelligence without hard dependency |
| [Graphify](https://github.com/Graphify-Labs/graphify), `48d7c0e832cd2d67d86850e716ddea16df6238ea` | Relationship graph spanning code/docs and provenance for extracted/inferred edges | Adopted as optional broad-context provider | `repository-investigation.md`, `integrations.md` | Complements pure code graphs; not required |
| [ClaudeKit](https://github.com/mrgoonie/claudekit-skills), `80113d86bc4407f105af40a2c4ea58194f7c370a` | Systematic debugging, root-cause tracing, verification-before-completion, specialist routing | Adopted selectively | `implementation-debugging.md`, `verification-review.md`, `collaboration-state.md` | Useful patterns without importing broad library scope |
| [Alireza Claude Skills](https://github.com/alirezarezvani/claude-skills), `19392f7a08264ed00486a251f5b2098321771f94` | Modular specialist skills and broad skill discoverability | Adopted structurally | `SKILL.md`, `collaboration-state.md` | Keeps core narrow and specialists modular |

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
