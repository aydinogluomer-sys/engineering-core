# engineering-core

[![Validate](https://github.com/aydinogluomer-sys/engineering-core/actions/workflows/validate.yml/badge.svg)](https://github.com/aydinogluomer-sys/engineering-core/actions/workflows/validate.yml)

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
├── .github/workflows/validate.yml
├── docs/
│   ├── claude-router.md
│   ├── deterministic-enforcement.md
│   └── l4-evaluation.md
├── evals/
│   ├── README.md
│   ├── activation/
│   ├── completion_summary.py
│   ├── run_l4_eval.py
│   ├── test_completion_summary.py
│   ├── test_l4_eval.py
│   └── scenarios/
├── scripts/
│   └── validate_repository.py
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
git clone https://github.com/aydinogluomer-sys/engineering-core.git
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

Natural selection is measured separately from explicit `/engineering-core` invocation. See [`evals/activation/README.md`](evals/activation/README.md) for positive, negative, and ambiguous datasets plus bounded candidate-description evaluation.

The latest bounded Haiku run observed candidate-description natural precision `1.00` and recall `0.50` across 12 positive and 8 negative prompts; four ambiguous prompts were reported separately. This is L4 sample evidence, not a routing guarantee. The retained runs and limitations are in [`docs/l4-evaluation.md`](docs/l4-evaluation.md).

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

For deployment-oriented control design, see [`docs/deterministic-enforcement.md`](docs/deterministic-enforcement.md). It covers permissions, sandboxes, hooks, command-guard failure modes, and test fixtures without installing or shipping a runnable guard.

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

The validation tools require Python 3.10 or newer. Static CI covers Python 3.10 and 3.14 on Linux and Windows.

Current design/validation history is recorded in [`implementation.md`](implementation.md).

## Validate the package

From the repository root:

```bash
python engineering-core/scripts/validate_skill.py engineering-core
python engineering-core/scripts/test_validate_skill.py
python evals/test_completion_summary.py
python evals/test_l4_eval.py
python evals/activation/test_activation_eval.py
python -m py_compile engineering-core/scripts/validate_skill.py engineering-core/scripts/test_validate_skill.py scripts/validate_repository.py evals/completion_summary.py evals/test_completion_summary.py evals/run_l4_eval.py evals/test_l4_eval.py evals/activation/run_activation_eval.py evals/activation/test_activation_eval.py
python scripts/validate_repository.py .
```

The package validator checks the exact distributable skill tree and statically observable policy properties. The repository validator separately checks public-repository links, fixtures, CI markers, placeholders, and obvious secret material. Neither proves runtime activation, security, correct root-cause discovery, or absence of scope creep.

## Live L4 evaluation

Live evaluation is intentionally local/manual because it invokes Claude Code and has time/cost implications. Each scenario gets a separate disposable Git repository and Claude process; a zero exit code is not enough to pass.

Run a cheap explicit-activation case first:

```bash
python evals/run_l4_eval.py --case small --model haiku --per-case-budget 0.35 --total-budget 0.35
```

See [`evals/README.md`](evals/README.md) for all-core execution and [`docs/l4-evaluation.md`](docs/l4-evaluation.md) for the append-only evidence record. Explicit activation and natural activation are reported separately. The optional router is not required by the harness.

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

## Current evidence status

- L1 structural validation: locally exercised; see the current execution record in [`implementation.md`](implementation.md).
- L2 policy lint: locally exercised; static heuristics are not behavioral proof.
- L3 adversarial policy traces: documented and audited; see the execution record for current counts/results.
- L4 live Claude Code behavior: see [`docs/l4-evaluation.md`](docs/l4-evaluation.md); cases are never implied by a green static validator.
- L5 longitudinal field evidence: not established.

The workflow is present for push, pull request, and manual dispatch. A local CI-equivalent pass is distinct from a hosted GitHub Actions pass; the badge reflects GitHub only after a pushed workflow runs.

## License

MIT. See [`LICENSE`](LICENSE).
