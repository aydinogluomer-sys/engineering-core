# Current validation status

Canonical status owner. Updated 2026-10-07 for the v5 failure-resistance candidate. Contract baseline, validated working-tree bytes, published Git identity, and hosted CI are deliberately separate.

## Identity and evidence state

| Identity | Current value | Meaning |
|---|---|---|
| Contract baseline | `ea65af9e81ef9f7c595c2fd1f05d13a3f08a5c45` | Clean `main` / `origin/main` observed before v5 implementation |
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
| Pressure campaign | NOT_RUN | Frozen live plan exists; no paid model call or exact spend authorization |
| Completion/report/event strictness | PASS | Existing schema-v3 completion and event contracts remain green |
| Trusted oracle and scope integrity | PASS | Evaluator-owned oracle and Git/scope negative controls remain green |
| Evidence freshness and continuation state | PASS | Relevant/unrelated staleness, resume identity, CAS, recovery, graph, and ownership tests |
| Team stage provenance and Two-Key scorer | PASS | Evaluator-owned stage records and fresh audit semantics remain green |
| Installer behavior | PASS | Fresh/no-op/update/drift/failure/rollback/anti-nesting tests |
| README architecture contract | PASS | Exactly fourteen numbered Mermaid blocks, local links, declarations, before/after table, evidence boundaries, and non-goals; mutation-tested validator |
| Fresh independent v5 audit | PASS | Final re-audit reconciled all prior pressure/provenance/manifest/evidence blockers and found no new blocker |
| TypeScript integration fixture | BLOCKED | Node exists; `tsc` command not found; no install attempted and no typecheck PASS claimed |
| PostgreSQL/RLS integration fixture | BLOCKED | `psql` command not found; no database PASS claimed |
| Browser interaction fixture | BLOCKED | Chrome/Edge/Chromium executable commands not detected; no browser PASS claimed |
| Live Haiku/Sonnet/Opus/Fable reliability matrix | NOT_RUN | Manifest requires runtime alias discovery, observed served identity, pressure cells, repetitions, provenance, and bounded spend |
| Seven-day longitudinal field reliability | NOT_RUN | Protocol exists; seven elapsed days and independent field audit not performed |
| GitHub branch protection | NOT_APPLIED | Prepared governance profile only; settings mutation was not requested |
| Tag / GitHub release | NOT_AUTHORIZED | No tag or release is created by this work |
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
- No unavailable stack, live, governance, publication, or longitudinal cell is promoted to PASS.

See the sanitized local bundle in [`../evidence/current/`](../evidence/current/) after generation and its `SHA256SUMS.json` manifest.
