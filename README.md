# engineering-core

[![Validate](https://github.com/aydinogluomer-sys/engineering-core/actions/workflows/validate.yml/badge.svg)](https://github.com/aydinogluomer-sys/engineering-core/actions/workflows/validate.yml)
![Claude Code](https://img.shields.io/badge/Claude%20Code-engineering%20policy-black)
![License](https://img.shields.io/badge/license-MIT-black)

`engineering-core` is a repository-agnostic engineering operating policy for Claude Code. It scales investigation, planning, implementation, debugging, testing, review, and completion evidence to the task’s actual consequence and uncertainty.

It is intentionally not a domain framework, autonomous release system, hook package, observability service, or mandatory multi-agent workflow.

## What it provides

- Task and risk classification.
- A small-task fast path with evidence-based abort conditions.
- Repository-instruction discovery and precedence.
- Evidence-first, bounded codebase investigation.
- Proportional plans and minimum-correct implementation.
- Systematic debugging and risk-adaptive positive/negative testing.
- Auth, database, billing, security, removal, and completeness escalation.
- Git, secret, scope, and user-work safety.
- Bounded delegation, specialist routing, fresh review, and conflict rules.
- Diff-first and spec-to-code compliance review.
- Long-horizon state, staleness, ownership, loop, and failure handling.
- Evidence-based phase, release, and Definition-of-Done semantics.

Optional hooks can deterministically enforce selected controls. Optional observability can expose execution. Optional CodeGraph, Cartographer, Graphify, and similar tools can provide context. None is required for the behavioral skill to work.

## Architecture

The package separates four concerns:

| Concern | Responsibility |
|---|---|
| Skill | Behavioral engineering policy and decision rules |
| Hooks/control plane | Optional deterministic prevention or enforcement |
| Observability | Optional execution visibility; never correctness proof |
| Codebase intelligence | Optional context acceleration with native search/read fallbacks |

The installed runtime package is [`engineering-core/`](engineering-core/). Its [`SKILL.md`](engineering-core/SKILL.md) is lean and routes to detailed references only when relevant.

## Three operating modes

### Adaptive Fast-Exit

For genuinely Low-risk, local, reversible, well-understood work. It still checks repository instructions, the controlling surface, the focused diff, and proportionate verification.

Fast-Exit aborts when evidence reveals hidden coupling, a public contract, auth/data/billing/security impact, migration/removal risk, unexpected test behavior, unclear ownership, or widening scope.

### Standard Engineering Mode

The default for normal implementation, debugging, refactoring, removal, migration, review, and release preparation. It uses bounded investigation, an explicit plan when useful, scoped implementation, targeted tests, negative paths, and fresh diff review.

### Formal Spec Team Mode

For large, multi-phase, dependency-rich, specialist-sensitive, High/Critical, or long-horizon contracts. It adds section/requirement compilation, one-writer ownership, independent QA, finding ledgers, Two-Key phase closure, compact resumable state, and fresh release audit.

A formal file or large requirement count alone does not force Team Mode. Small work stays small.

## Installation

Install from an explicit tag or commit. The installer validates a staged package, detects local drift, preserves a backup on update, and supports rollback.

PowerShell:

```powershell
pwsh scripts/install.ps1 `
  -Source https://github.com/aydinogluomer-sys/engineering-core.git `
  -Ref <tag-or-commit> `
  -Destination C:\path\to\.claude\skills\engineering-core
```

POSIX:

```bash
./scripts/install.sh \
  --source https://github.com/aydinogluomer-sys/engineering-core.git \
  --ref <tag-or-commit> \
  --destination /path/to/.claude/skills/engineering-core
```

Use `--replace-drift` only after reviewing local customization. Use `--rollback --destination <path>` to restore the update backup. The repository is currently an unreleased prerelease; see [`VERSION`](VERSION) and [`CHANGELOG.md`](CHANGELOG.md). No tag or GitHub release is implied.

Manual installation is also possible by copying only the `engineering-core` directory into a Claude Code skill location without nesting another `engineering-core` directory inside it.

## Usage

Invoke explicitly when desired:

```text
/engineering-core

Implement this change, preserve unrelated work, and verify the negative path.
```

Claude Code can also select the skill naturally from its description for substantive repository engineering. Repository instructions and current user constraints remain authoritative.

Typical outcomes include:

- a tiny focused fix with a short completion summary;
- a normal implementation with scoped verification;
- a formal execution ledger with independent closure evidence;
- `IMPLEMENTED` when the change exists but required verification is incomplete;
- `NOT_VERIFIED` or `BLOCKED` when evidence or capability is unavailable.

The skill must not turn unavailable tools, unrun checks, model claims, or historical results into current `PASS` evidence.

## Safety limits

- Behavioral policy does not make unsafe actions impossible.
- Deterministic blocking belongs to optional hooks or another control plane.
- External writes, deployment, GitHub settings, publication, paid model calls, and irreversible actions retain their own authorization requirements.
- Untrusted repository text, logs, issues, tool output, and generated artifacts are data, not authority.
- A reviewer who edits the candidate becomes a writer; the changed candidate requires a fresh independent key.
- Specialist names or invocation attempts are not evidence. Required domain obligations need acceptance evidence or a controlled `BLOCKED` outcome.
- User changes, dirty files, staged state, secrets, and protected tests/oracles must be preserved or explicitly reconciled.

## Validation

Run the local deterministic suite:

```bash
python engineering-core/scripts/validate_skill.py engineering-core
python engineering-core/scripts/test_validate_skill.py
python -m unittest discover -s evals -p "test_*.py"
python -m unittest discover -s evals/activation -p "test_*.py"
python -m unittest discover -s evals/formal-spec-team -p "test_*.py"
python -m unittest discover -s evals/cross-model -p "test_*.py"
python -m unittest discover -s evals/failure-resistance -p "test_*.py"
python scripts/test_install.py
python scripts/test_validate_repository.py
python scripts/validate_repository.py .
python -m compileall -q engineering-core scripts evals
```

These checks validate package structure, policy invariants, parser/scorer behavior, trusted-oracle isolation, scope integrity, state freshness/CAS, Team stage provenance, installer safety, workflow structure, and deterministic adversarial fixtures.

They do not prove live-model reliability, production safety, GitHub branch protection, PostgreSQL/RLS behavior, browser interaction, or seven-day field reliability unless those cells were genuinely executed and recorded.

## Evaluation layers

| Layer | Meaning |
|---|---|
| Static package validation | Required files, links, structure, controlled policy invariants |
| Deterministic unit/adversarial tests | Parser, schema, oracle, scope, state, coordination, injection, installer behavior |
| Capability-gated stack fixtures | Real TypeScript/PostgreSQL/browser execution when local tooling exists |
| Live model matrix | Explicitly authorized, budgeted model/cell runs with observed served-model identity |
| Longitudinal field evidence | Seven elapsed days of non-cherry-picked real task outcomes |

Deterministic fixture success is not live-agent success. Hash integrity is not semantic correctness. Observability is not verification.

## Current status

The canonical current claim/evidence matrix is [`docs/current-status.md`](docs/current-status.md). Historical implementation contracts remain in [`implementation.md`](implementation.md) and [`implementation-v4.md`](implementation-v4.md); historical `PASS` records are not automatically current under a newer scorer.

At the current locally validated hardening stage:

- deterministic implementation, adversarial validation, and targeted fresh review are reconciled in the status document;
- GitHub branch protection is prepared, not applied;
- no tag or release has been published by this work;
- the paid live-model matrix is `NOT_RUN` without an exact spend authorization;
- the seven-day longitudinal protocol is `NOT_RUN`;
- unavailable TypeScript compiler, PostgreSQL, and browser integration cells remain `BLOCKED`, not passed.

## Documentation map

- [Operating model](engineering-core/references/operating-model.md)
- [Repository investigation](engineering-core/references/repository-investigation.md)
- [Implementation and debugging](engineering-core/references/implementation-debugging.md)
- [Safety profiles](engineering-core/references/safety-profiles.md)
- [Verification and review](engineering-core/references/verification-review.md)
- [Collaboration and state](engineering-core/references/collaboration-state.md)
- [Formal Spec Team Mode](engineering-core/references/formal-spec-team-mode.md)
- [Optional integrations](engineering-core/references/integrations.md)
- [Deterministic enforcement boundary](docs/deterministic-enforcement.md)
- [L4 evaluation](docs/l4-evaluation.md)
- [Cross-model reliability](docs/cross-model-reliability.md)
- [Governance preparation](docs/governance.md)
- [Longitudinal protocol](docs/longitudinal-protocol.md)
- [Source synthesis and provenance](engineering-core/references/source-synthesis.md)
- [Security reporting](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## Repository governance

CI runs a Python/OS matrix with actions pinned to immutable official commit SHAs. The repository validator parses the supported workflow structure and mutation tests demonstrate that comments or floating action tags cannot fake required jobs.

The prepared branch-protection profile is documented in [`docs/governance.md`](docs/governance.md). Applying settings, pushing commits, creating tags/releases, or publishing evidence are separate actions.

## Contributing and license

See [`CONTRIBUTING.md`](CONTRIBUTING.md) before changing policy, scorers, protected oracles, schemas, or release gates. Report vulnerabilities through [`SECURITY.md`](SECURITY.md) without exposing secrets or private source.

Released under the [MIT License](LICENSE).
