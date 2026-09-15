# engineering-core

A risk-adaptive engineering operating policy for Claude Code.

`engineering-core` gives Claude Code a reusable software-engineering discipline for implementation, debugging, refactoring, removal, testing, review, migration, and release work.

Instead of forcing every task through the same heavyweight workflow, it scales investigation, planning, safety, testing, and review to the actual consequence and uncertainty of the change.

## Why engineering-core?

Coding agents often fail in two opposite ways:

- they move too quickly on changes that require deeper investigation; or
- they turn small, obvious fixes into unnecessarily expensive workflows.

`engineering-core` uses a different principle:

> Use the minimum engineering ceremony required by the risk of the task, and require stronger evidence as consequence increases.

A typo should remain a tiny task.

A one-line authorization, billing, database, or production change should not be treated as low risk merely because the diff is small.

## What it does

The core operating loop is:

```text
CLASSIFY
→ DISCOVER
→ INVESTIGATE
→ PLAN
→ IMPLEMENT
→ VERIFY
→ REVIEW
→ COMPLETE
```

For Low-risk local work, investigation and planning compress into a fast path. Higher-risk work expands into explicit repository investigation, invariants, negative-path testing, security escalation, fresh review, release gates, and evidence-based completion.

Key behaviors include:

- risk-adaptive workflow selection;
- repository instruction discovery;
- evidence-first bounded codebase investigation;
- minimum-correct implementation and scope control;
- systematic root-cause debugging;
- loop and failure classification;
- risk-adaptive positive and negative testing;
- security, database, authentication, authorization, and billing escalation;
- Git and secret safety;
- bounded subagent delegation;
- fresh review for sufficiently risky changes;
- formal specification / `implementation.md` execution;
- removal and completeness audits;
- long-horizon state and resume discipline;
- optional codebase-intelligence integrations with native fallbacks;
- evidence-based Definition of Done.

## Why the runtime entrypoint is intentionally small

`SKILL.md` is the runtime dispatcher, not the full handbook.

It keeps only the universal lifecycle, high-value invariants, fast path, safety boundary, and conditional routes that should remain cheap and resilient during long sessions.

Detailed procedures live in `references/`, and concrete illustrations live in `examples/`. Claude loads those details only when the task requires them.

This progressive-disclosure design reduces default context cost, avoids repeating specialist procedures, and keeps the core useful for both tiny fixes and long hardening work.

## Repository structure

```text
.
├── README.md
├── LICENSE
├── .gitignore
├── implementation.md
├── docs/
│   └── claude-router.md
└── engineering-core/
    ├── SKILL.md
    ├── examples/
    │   ├── small-fix.md
    │   ├── normal-feature.md
    │   ├── high-risk-change.md
    │   ├── removal-task.md
    │   └── large-spec-execution.md
    ├── references/
    │   ├── operating-model.md
    │   ├── repository-investigation.md
    │   ├── implementation-debugging.md
    │   ├── verification-review.md
    │   ├── safety-profiles.md
    │   ├── collaboration-state.md
    │   ├── integrations.md
    │   ├── source-synthesis.md
    │   └── evaluation-scenarios.md
    └── scripts/
        ├── validate_skill.py
        └── test_validate_skill.py
```

## Installation

### Personal skill

Clone this repository:

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/engineering-core.git
```

macOS / Linux:

```bash
mkdir -p ~/.claude/skills
cp -R engineering-core/engineering-core ~/.claude/skills/engineering-core
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse ".\engineering-core\engineering-core" "$HOME\.claude\skills\engineering-core"
```

Restart Claude Code if necessary.

### Project-scoped skill

Copy the inner `engineering-core/` directory to:

```text
<project>/.claude/skills/engineering-core/
```

The installed skill directory should contain `SKILL.md`, `examples/`, `references/`, and `scripts/`.

## Usage

The skill is model-invocable.

Typical requests include:

```text
Fix this race condition.
Implement this feature.
Remove this subsystem completely.
Review and fix this authorization flow.
Implement this implementation.md phase by phase.
Prepare this branch for release.
```

`engineering-core` does not replace specialist domain skills. It provides cross-cutting process, evidence, risk, safety boundaries, verification, and completion semantics.

## Optional project routing

If you want stronger project-level guidance so `engineering-core` is consistently considered for substantive engineering work, see:

[`docs/claude-router.md`](docs/claude-router.md)

The router is optional and is not deterministic enforcement.

## Optional integrations

External tooling is never required.

When already available or explicitly requested, the core can cooperate with codebase-intelligence systems such as:

- CodeGraph;
- Cartographer;
- Graphify;
- language-server or repository indexes.

They are context providers, not unquestioned sources of truth.

Similarly:

- hooks/permissions provide deterministic enforcement;
- observability provides execution visibility;
- specialist skills provide domain expertise.

Those responsibilities remain separate.

## Validation model

The project distinguishes five evidence levels:

| Level | Evidence |
|---|---|
| L1 | Structural validation |
| L2 | Policy lint |
| L3 | Manual/adversarial scenario evaluation |
| L4 | Live Claude Code behavioral evaluation |
| L5 | Longitudinal real-world field evaluation |

A lower level never claims a higher-level guarantee.

Current design/validation history is recorded in [`implementation.md`](implementation.md).

## Validate the package

From the repository root:

```bash
python engineering-core/scripts/validate_skill.py engineering-core
python engineering-core/scripts/test_validate_skill.py
python -m py_compile engineering-core/scripts/validate_skill.py engineering-core/scripts/test_validate_skill.py
```

The validator checks structural and statically observable policy properties only. It does not prove runtime activation, security, correct root-cause discovery, or absence of scope creep.

## What engineering-core is not

It is not:

- a deterministic security sandbox;
- a destructive-command blocker;
- a replacement for Claude Code permissions or hooks;
- a mandatory multi-agent framework;
- a code graph;
- a security scanner;
- a domain-specific framework;
- a requirement to create a plan file for every task.

Its responsibility is:

`risk + evidence + scope + implementation discipline + verification + review + completion semantics`

## Design influences

The design synthesizes principles from:

- official Claude Code guidance;
- Superpowers;
- gstack;
- Trail of Bits skills;
- Safety Net / Destructive Command Guard concepts;
- Claude Code Hooks Mastery;
- Multi-Agent Observability;
- CodeGraph;
- Cartographer;
- Graphify;
- ClaudeKit;
- Alireza Claude Skills.

See [`engineering-core/references/source-synthesis.md`](engineering-core/references/source-synthesis.md) for the adopted / modified / rejected mapping.

## Development status

The policy architecture is structurally mature.

Before calling the project `v1.0.0`, representative L4 live Claude Code evaluation and subsequent field use are recommended.

A reasonable first public release is `v0.9.0`.

## License

MIT. See [`LICENSE`](LICENSE).
