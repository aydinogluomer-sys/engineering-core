# Current validation status

Canonical status owner. Updated 2026-10-08 during v6 evidence closure. Contract baseline, validated working-tree bytes, published Git identity, integration evidence, hosted CI, live-model evidence, governance, publication, and L5 are deliberately separate.

## Identity and evidence state

| Identity | Current value | Meaning |
|---|---|---|
| Contract baseline | `713f76e9444079186a5d6a9fa9e3a85188c015be` | Clean `main` / `origin/main` observed before v6 evidence closure |
| Validated candidate | `evidence/current/evidence.json` candidate manifest and SHA-256 digest | Exact repository bytes covered by the latest local bundle; not a Git commit identity |
| Published v5 implementation commit | `daa92b55f784a23210bce84b8ff10b42bf8c5131` | Pushed to `origin/main` after local gates and fresh audit |
| Hosted CI for v5 implementation | GitHub Actions run `37747462471`, PASS | All Ubuntu/Windows × Python 3.10/3.14 jobs passed |
| Final status-record commit | This document's commit, followed by post-push observation | A committed file cannot embed its own future Git object ID; final remote equality and CI are reported from GitHub after push |

The evidence bundle records its repository parent commit plus a complete candidate byte manifest. A later commit changes Git metadata and may change the evidence files themselves; therefore local evidence binds candidate bytes rather than pretending to be evidence for an unknown future commit.

## Claim matrix

| Claim | Status | Current evidence / limitation |
|---|---|---|
| Runtime skill structure and policy lint | PASS | Lean 82-line `SKILL.md`; five new policy IDs have canonical ownership; 30 validator mutation tests |
| Adversarial decision and gate-integrity policy | PASS | Canonical verification/review policies, worked example, L3 positive/negative traces |
| External and orchestration provenance | PASS | Version-sensitive source reconciliation and one-hop/direct-evidence rules at canonical owners |
| Competing-hypothesis policy | PASS | Narrow eligibility, discriminating matrix, bounded stop rule, native fallback |
| L3 failure-resistance matrix | PASS | Scenarios 114–137 are structurally required by the repository validator |
| Core L4 harness | PASS (STATIC) | Existing evaluator/oracle/scope harness plus deterministic scorer tests |
| Pressure harness | PASS (STATIC) | Eight pressure profiles; mutation tests for forged dispositions, visible-gate edits, stale evidence, skipped QA, release evidence, sunk cost, authority, and orchestration |
| Pressure campaign | NOT_AUTHORIZED | Claude Code 2.1.289 and bounded harness controls observed; no paid model call because numeric `MAX_TOTAL_SPEND_USD` is unset |
| Completion/report/event strictness | PASS | Existing schema-v3 completion and event contracts remain green |
| Trusted oracle and scope integrity | PASS | Evaluator-owned oracle and Git/scope negative controls remain green |
| Evidence freshness and continuation state | PASS | Relevant/unrelated staleness, resume identity, CAS, recovery, graph, and ownership tests |
| Team stage provenance and Two-Key scorer | PASS | Evaluator-owned stage records and fresh audit semantics remain green |
| Installer behavior | PASS | Fresh/no-op/update/drift/failure/rollback/anti-nesting tests |
| README architecture contract | PASS | Exactly fourteen numbered Mermaid blocks, local links, declarations, before/after table, evidence boundaries, and non-goals; mutation-tested validator |
| Fresh independent v5 audit | PASS | Final re-audit reconciled all prior pressure/provenance/manifest/evidence blockers and found no new blocker |
| TypeScript integration | PASS | Real TypeScript 7.0.2 from an isolated npm cache; bad fixture fails with TS2322, fixed fixture passes strict no-emit compilation, no suppression directive |
| PostgreSQL/RLS integration | PASS | Real PostgreSQL 17.6 in disposable `postgres:17.6-alpine`; evaluator-owned role, grant, policy, owner, tenant read/write, and service probes; container removed after run |
| Browser interaction | PASS | Playwright 1.64.0 with real Chrome 154.0.8037.98; evaluator-owned DOM, click, disabled state, keyboard/focus, navigation, and console probes |
| Live Haiku/Sonnet/Opus/Fable reliability matrix | NOT_AUTHORIZED | CLI help advertises Fable/Opus/Sonnet; Haiku and effective identities remain unobserved without invocation; numeric `MAX_TOTAL_SPEND_USD` is unset; zero paid calls |
| Seven-day longitudinal field reliability | IN_PROGRESS | Started `2026-10-08T17:27:27.790565Z` for candidate `4de42795e3343c0bc0d81a32627ab3dbff17dc1a`; earliest completion `2026-10-15T17:27:27.790565Z`; zero post-freeze tasks currently captured |
| GitHub branch protection | APPLIED | API read-back: strict four-cell hosted checks, administrator enforcement, linear history, force pushes/deletion blocked, no solo-maintainer review lockout; evidence in `evidence/current/governance.json` |
| Tag / GitHub release | BLOCKED | Authorized only after all release gates; current live-model campaign lacks `MAX_TOTAL_SPEND_USD`, so no tag or prerelease may be created |
| Repository push to `main` | PASS | Authorized implementation commit pushed; hosted matrix passed; final status-record commit is verified after its push |

## Current local validation

The canonical command set was executed after the implementation and documentation edits. It passed: skill validator; 30 skill-validator tests; 73 core eval tests; 14 activation tests; 16 Team tests; 20 cross-model tests; 5 failure-resistance tests; 4 installer tests; 8 repository-validator tests; repository validation; and compileall. The final evidence-bundle generation reruns this full set and becomes the current byte-level record.

One earlier ad-hoc invocation used direct `unittest` module paths incompatible with this repository's import layout and produced two import errors. The canonical discovery invocations immediately replaced it and passed; the failed command is not reported as a product or gate PASS.

## Evidence boundaries

- Behavioral policy is not deterministic prevention; optional hooks/control-plane enforcement is separate.
- Observability is execution visibility, not correctness proof.
- CodeGraph, Cartographer, Graphify, and similar providers are optional context sources with native fallbacks.
- Model-authored artifacts are claims until evaluator-owned records and protected checks reconcile them.
- Static fixtures and mutation tests do not prove live-agent or cross-model reliability.
- Requested aliases do not prove the effective served model.
- Hashes prove byte integrity, not semantics or reviewer independence.
- No unavailable live, governance, publication, or longitudinal cell is promoted to PASS. Stack PASS is backed by the real tool report in `evidence/current/integrations.json`.

See the sanitized local bundle in [`../evidence/current/`](../evidence/current/) after generation and its `SHA256SUMS.json` manifest.
