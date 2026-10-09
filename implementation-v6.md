# Engineering Core v6 Evidence Closure Contract

Status: IN_PROGRESS

Authoritative request: current evidence, integration, governance, and prerelease closure

Starting commit: `713f76e9444079186a5d6a9fa9e3a85188c015be`

This contract implements evidence closure without redesigning the runtime policy. A checked item is permitted only after the named command, read-back, or independent audit has produced retained evidence. Historical evidence is never promoted to current evidence.

## Phase 0 — Rebaseline and constraints

- [x] Fetch `origin` and verify the clean `main` worktree starts at the recorded remote commit.
- [x] Discover local Node/npm, TypeScript, PostgreSQL/container, browser, Claude CLI, GitHub CLI, and authentication capabilities.
- [x] Record that billable model calls are prohibited until the user supplies `MAX_TOTAL_SPEND_USD`.
- [ ] Confirm an explicit numeric `MAX_TOTAL_SPEND_USD` before any paid live-model invocation.

Gate: repository ownership is reconciled, no unknown work is overwritten, and tool limitations are facts rather than inferred PASS claims.

## Phase 1 — Real stack integration harness

Build evaluator-owned, candidate-independent oracles with exact tool versions and disposable state.

### TypeScript

- [x] Provision an exact TypeScript version in an isolated test cache; do not add it as a runtime dependency.
- [x] Make the known-bad fixture fail with the expected relevant compiler diagnostic.
- [x] Make the corrected fixture pass without suppression directives or weakened compiler settings.
- [x] Bind evidence to fixture and oracle hashes plus Node/npm/TypeScript versions.

### PostgreSQL/RLS

- [x] Provision real disposable PostgreSQL using an explicit version; never touch production or user databases.
- [x] Verify the intentionally broken baseline exposes or mutates cross-tenant data.
- [x] Verify the corrected policy permits tenant A and the authorized administrative path while denying tenant B read and write access.
- [x] Independently inspect grants, policy enablement/force state, role/session context, owner behavior, and direct table access.
- [x] Destroy disposable database/container state and retain sanitized version/image/digest/port/fixture evidence.

### Browser

- [x] Provision an exact Playwright version in an isolated test cache or use a discovered compatible browser executable.
- [x] Make the known-bad page fail evaluator-owned DOM, click, keyboard/focus, disabled/authorization, and console assertions.
- [x] Make the corrected page pass the same real browser oracle.
- [x] Bind evidence to fixture/oracle hashes and Node/Playwright/browser versions.

Gate: each PASS originates from the real system that owns the semantics. Missing capability remains BLOCKED; mocks, static parsing, screenshots, and candidate prose cannot close a cell.

## Phase 2 — Evidence integrity and repository validation

- [x] Add unit tests for report validation, baseline/fixed polarity, suppression detection, hash integrity, and unavailable-capability behavior.
- [x] Teach repository validation to require the integration runner, trusted oracles, protected fixtures, ignored tool caches, and sanitized current evidence.
- [x] Extend the evidence builder so current integration results are imported only when schema-valid, hash-valid, tool-observed, and bound to the candidate tree/commit.
- [x] Update failure-resistance documentation, current status, L4/cross-model reports, changelog, and README evidence sections without changing the fourteen architecture diagrams.
- [x] Start the L5 ledger with a real UTC timestamp, candidate identity, required fields, and state `IN_PROGRESS`; do not backdate or claim seven elapsed days.

Gate: the canonical local suite passes, secret/cache scan is clean, and generated evidence distinguishes local, integration, live-model, governance, publication, and longitudinal states.

## Phase 3 — Candidate freeze and hosted CI

- [x] Run the complete canonical validation command set and all three real integrations.
- [x] Inspect `git diff`, generated evidence, ignored/untracked files, and tracked content for secrets, binaries, caches, database files, and transcripts.
- [x] Commit deterministic implementation and evidence schema changes, record the candidate SHA, and ensure a clean worktree.
- [x] Push the candidate to `main` and require the four hosted OS/Python jobs to pass for that exact SHA.

Gate: expensive/live evidence may only attach to the frozen candidate SHA. Runtime-policy changes invalidate affected evidence.

## Phase 4 — Budget-gated live campaign

Dependency: Phase 3 plus explicit numeric `MAX_TOTAL_SPEND_USD`.

- [ ] Discover actual Claude Code model identifiers and whether effective model identity and incremental cost are observable.
- [ ] Produce a worst-case campaign budget table and verify it is within the user-set cap before invocation.
- [ ] Run the current activation, mode-selection, Core L4, Team L4, and eight-family pressure suites with the required models and bounded repetitions.
- [ ] Preserve every failure; classify it at the correct policy/scorer/fixture/environment/model layer; never retry for a lucky result.
- [ ] Record requested/effective model truthfully, including `UNOBSERVED` and fallback states.
- [ ] Commit current candidate-bound reports without averaging away per-model failures.

Gate: Sonnet, Opus, and Fable meet all mandatory current gates; Haiku is reported honestly. If authorization remains absent, these cells remain `NOT_AUTHORIZED`, publication remains blocked, and no paid call occurs.

## Phase 5 — Governance

- [x] Read and save the current `main` branch-protection configuration before mutation.
- [x] Derive required status-check contexts from the successful hosted workflow.
- [x] Apply strict required checks, block force pushes and deletion, and enable administrator enforcement only when it does not create lockout; do not require reviews for a solo-maintainer flow.
- [x] Read back the effective configuration and retain sanitized evidence.

Gate: the observed GitHub configuration matches the intended policy. Governance evidence is separate from behavioral skill policy and local checks.

## Phase 6 — Fresh audit and publication

Dependencies: Phases 1–5; L5 may remain `IN_PROGRESS`.

- [ ] Run final canonical validation and hosted CI against the exact final candidate SHA.
- [ ] Give a fresh independent reviewer the original requirements, base-to-head diff, current evidence, integration reports, live reports, governance read-back, and release plan without priming a verdict.
- [ ] Resolve all findings and obtain `RELEASE_VERIFIED`; otherwise retain `RELEASE_NOT_VERIFIED` or `RELEASE_BLOCKED`.
- [ ] Create the annotated tag derived from `VERSION` at the exact audited SHA without moving any existing tag.
- [ ] Publish a GitHub prerelease and read back tag, target SHA, prerelease flag, URL, and timestamp.
- [ ] Push all verified commits and reconcile final documentation/evidence.

Gate: no tag or release exists unless every mandatory current gate is supported by fresh evidence and the independent verdict is `RELEASE_VERIFIED`.

## Final audit

- [ ] Repository HEAD, `origin/main`, hosted CI SHA, evidence candidate SHA, tag target, and release target are identical.
- [ ] TypeScript, PostgreSQL/RLS, and browser cells contain real tool/version evidence and correct baseline/fixed polarity.
- [ ] Live matrices are current, candidate-bound, model-specific, within budget, and retain failures.
- [ ] Branch protection matches read-back evidence.
- [ ] L5 is `IN_PROGRESS` until seven real elapsed days and independent final analysis exist.
- [ ] Final report uses the required A–L structure and makes no unsupported completion claim.

## Execution record

| Time (UTC) | Phase | Evidence | Result |
|---|---|---|---|
| 2026-10-08 | 0 | `git fetch origin`; clean `main`; local HEAD and `origin/main` both `713f76e9444079186a5d6a9fa9e3a85188c015be` | PASS |
| 2026-10-08 | 0 | Node/npm/npx present; global `tsc`, `psql`, `postgres`, Podman, and Claude CLI absent; Docker CLI present but daemon unavailable; Chrome and Edge discovered by absolute path | PASS |
| 2026-10-08 | 0 | No user-set numeric `MAX_TOTAL_SPEND_USD` observed | BILLABLE CALLS NOT AUTHORIZED |
| 2026-10-08 | 1 | First real stack run: TypeScript and browser passed; PostgreSQL fixed behavior passed eight of nine checks, but scalar output parsing misread `SET` command output | FAIL — scorer classification |
| 2026-10-08 | 1 | Corrected evaluator scalar parsing without changing the fixture/gate; reran once; TypeScript 7.0.2, PostgreSQL 17.6/RLS, and Playwright 1.64.0 + Chrome 154.0.8037.98 all showed bad-fails/good-passes polarity | PASS |
| 2026-10-08 | 2–3 | Canonical 11-command suite, 6 failure-resistance tests, repository mutation tests, repository validator, compileall, evidence builder, diff check, and artifact scan | PASS |
| 2026-10-08 | 3 | Deterministic candidate committed as `4de42795e3343c0bc0d81a32627ab3dbff17dc1a`; real integrations rerun against its clean checkout | PASS |
| 2026-10-08T17:27:27.790565Z | 2 | L5 ledger started for candidate `4de42795e3343c0bc0d81a32627ab3dbff17dc1a`; earliest possible seven-day completion `2026-10-15T17:27:27.790565Z`; zero post-freeze tasks captured | IN_PROGRESS |
| 2026-10-08 | 3 | Hosted run `37817095051`: Ubuntu/Python 3.14 passed; three cells exposed CRLF-sensitive protected hashes and Python 3.10 rejection of seven-digit fractional timestamps | FAIL — environment/scorer portability |
| 2026-10-09 | 3 | Hosted run `37817693386` on commit `295e452986a5c4d9afae3d1d01083eb539092579`: Ubuntu/Windows × Python 3.10/3.14 | PASS |
| 2026-10-09 | 5 | Pre-state 404 unprotected; applied strict four-context checks, admin enforcement, linear history, force-push/deletion blocks, no required reviews; API read-back matched | APPLIED |
| 2026-10-09 | 4 | Claude Code 2.1.289/auth capability and `--max-budget-usd` observed without model invocation; manifest worst-case `$250.00`; numeric user cap remains unset; paid calls/spend remain zero | NOT_AUTHORIZED |
