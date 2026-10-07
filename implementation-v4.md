# Engineering Core v4 — Active Failure-Resistance Plan

Source contract: `implementation (3).md`, supplied 2026-10-02 and based on commit `6940e92aa1164c6b857d4bf7de9fbc622806ec17`.

This file is the active execution ledger. Historical plans and evidence remain in `implementation.md`; this file does not rewrite them. A checked item requires current evidence. Static fixture success, repository governance, live-model reliability, longitudinal evidence, and publication remain separate claims.

## Decision locks

- DL-01 through DL-14 from the source contract are binding.
- Preserve the three runtime modes and the lean repository-agnostic skill.
- Do not install deterministic enforcement, MCP, hooks, or network services into the runtime package.
- Keep evaluator-owned truth outside candidate write scope; model-authored artifacts remain claims.
- Do not treat an unrun check, unavailable capability, historical PASS, or requested model alias as current proof.
- Paid model calls, repository settings, push/merge/tag/release, and deployment require separate authorization.

## Baseline

| Field | Current evidence |
|---|---|
| Branch / HEAD | `main` / `6940e92aa1164c6b857d4bf7de9fbc622806ec17` |
| Worktree / remote | clean; `origin/main` equal at baseline |
| Repository instructions | no root or nested `AGENTS.md` / `CLAUDE.md` found |
| Capabilities | Python 3.14.6, Git 2.55.0, Node 26.3.0, Claude Code 2.1.287, GitHub CLI 2.98.0; PostgreSQL CLI unavailable; browser executable not detected |
| Required baseline suite | PASS: 28 validator, 14 completion, 6 core scorer, 14 activation, 14 Team, 15 cross-model tests; both validators, compileall, and diff check PASS |

## Dependency-ordered work units

1. **WORK-A — trusted oracle and scope integrity** (`EC-001`, `EC-020`, `EC-029`). Build evaluator-owned oracle execution, immutable oracle/scope manifests, robust Git inventory, and P0 test-cheating negative controls.
2. **WORK-B — evaluator-owned Team stages and closure** (`EC-002`–`EC-008`). Derive Two-Key/fresh-audit/finding closure from stage records, current hashes, source reconciliation, and trusted checks rather than artifact booleans or counts.
3. **WORK-C — strict completion/report/event contracts** (`EC-009`–`EC-017`). Add schema v3, legacy read adapters, exact types, completeness/partial semantics, provenance recomputation, and controlled malformed-event behavior.
4. **WORK-D — shared runner safety core** (`EC-018`, `EC-019`, `EC-046`, `EC-047`). Centralize bounded limits, reserves, redaction, CLI preflight, measurement-vs-quality gates, and deterministic nonzero `--require-gate` behavior.
5. **WORK-E — operational independence and trust boundaries** (`EC-032`, `EC-033`, `EC-038`–`EC-040`). Link runtime policy to concrete reviewer/specialist/injection/budget protocols without burdening Low work.
6. **WORK-F — evidence freshness and state ownership** (`EC-024`, `EC-034`–`EC-037`). Implement stdlib evidence/state validation, relevant-manifest staleness, atomic compare-and-swap, dependency validation, and one-writer transfer records.
7. **WORK-G — deterministic behavior fixtures** (`EC-025`–`EC-028`, `EC-038`). Add routing transition, coordination, specialist, injection, and locally supported stack fixtures. Unsupported PostgreSQL/browser cells remain `BLOCKED`, never simulated as live PASS.
8. **WORK-H — governance and safe distribution preparation** (`EC-041`–`EC-045`, `EC-050`). Add version/changelog, fixed-ref installer with rollback tests, structurally validated SHA-pinned CI, and maintainer governance/security/contribution files. Do not mutate GitHub settings or publish.
9. **WORK-I — concise current documentation and evidence bundle** (`EC-031`, `EC-048`, `EC-049`, `EC-050`). Establish one current-status owner, archive/link history, document source provenance and limits, and build a sanitized hashed local evidence bundle.
10. **WORK-J — live/longitudinal preparation** (`EC-021`–`EC-023`, `EC-030`). Freeze a bounded run manifest, sampling/statistics helpers, and seven-day field protocol. Without exact spend authorization, live cells remain `NOT_RUN` and model reliability remains unverified.
11. **FINAL — independent release audit.** Fresh reviewer receives the source contract, baseline-to-current diff, EC ledger, Decision Locks, oracle/isolation manifest, tests, evidence bundle, and explicit external-action ledger.

## Acceptance gates

### WORK-A

- [x] P0 candidate can weaken/delete visible tests and forge QA artifacts yet trusted scoring returns FAIL.
- [x] Correct candidate with untouched evaluator-owned oracle returns PASS.
- [x] Scope inventory detects staged/unstaged/untracked/deleted/renamed/ignored manipulation, Git errors, protected dirty-file drift, HEAD/index drift, and forbidden dependency/config changes.
- [x] Oracle/isolation limitations are explicit; no malicious-code sandbox guarantee is claimed.

### WORK-B

- [x] Stage records are evaluator-owned and bind role/run/session/spec/candidate hashes and evidence pointers.
- [x] Process counts and artifact booleans cannot manufacture implementation, independent, or fresh-audit keys.
- [x] Findings, blockers, deferrals, sections, requirements, orphan diffs, and universal completion claims reconcile against source and current evidence.
- [x] Same-stage relabeling, stale hashes, fake `VERIFIED_FIXED`, premature release, and empty-evidence coverage fail.

### WORK-C/D

- [x] Completion parser rejects blank values and fenced/example summaries while preserving supported human-readable forms.
- [x] Schema v3 and stdlib validator reject bool-as-number, non-finite/negative values, empty required strings, duplicates, wrong scenario sets, invalid provenance, malformed events, and unmarked partial reports.
- [x] Every runner records reserved/observed/accounted cost and charges reserve when cost is unknown or an invocation later raises.
- [x] `evaluation_completed` and `quality_gate_passed` are distinct; `--require-gate` fails closed.
- [x] Common recursive redaction and tracked-text scanning pass synthetic secret tests without flagging pattern definitions as credentials.
- [x] CLI capability preflight is non-billable and unsupported capability becomes controlled `BLOCKED`.

### WORK-E/F

- [x] Reviewer and specialist protocols preserve authority boundaries and require a new independent key after meaningful reviewer fixes.
- [x] Prompt-injection boundary fixtures reject fake authority, secret requests, test weakening, scope expansion, and premature closure.
- [x] Evidence binds requirement, actor, command, time, source/spec/environment/output hashes, limitations, and status.
- [x] Relevant dirty changes stale dependent evidence; unrelated changes do not.
- [x] Atomic state CAS, recovery, dependency-cycle/missing/self-loop detection, and ownership transfer conflicts are tested.

### WORK-G

- [x] Routing-transition, parallel-ownership, specialist, and injection fixture baselines fail and known-good candidates pass.
- [ ] TypeScript fixture runs a real local typecheck/acceptance oracle.
- [x] PostgreSQL/RLS and browser interaction cells are genuinely executed or explicitly `BLOCKED` from full-stack claims.
- [x] Deterministic simulation and live-agent evidence remain distinct.

### WORK-H/I/J

- [x] Installer fresh/update/no-op/drift/explicit-replace/rollback tests pass without nested installs or silent customization loss.
- [x] CI actions use verified immutable SHAs; workflow structure and required matrix commands are parsed, not accepted from substring markers alone.
- [x] Governance files use verified owner/contact facts; branch protection remains prepared-not-applied unless separately authorized.
- [x] README/current status/history/source provenance and sanitized evidence bundle reconcile with executable evidence.
- [x] Confirmatory live run manifest fixes models, budgets, cases, samples, repetitions, Wilson intervals, and stopping rules before results.
- [x] Live model and seven-day longitudinal cells remain `NOT_RUN` absent exact authorization and elapsed field evidence.

## EC coverage ledger

Every row starts unchecked. `VERIFIED` requires implementation evidence plus an independent key; `IMPLEMENTED` means the builder-side change exists but independent closure is pending.

| EC / source | Acceptance | Work | Status | Implementation/current evidence | Independent review / blocker |
|---|---|---|---|---|---|
| EC-001 / AUD-01 | Candidate-visible test weakening cannot pass | A | VERIFIED | `evals/trust.py`, `test_trust.py` | Fresh audit + adversarial suite PASS |
| EC-002 / AUD-02 | Two-Key binds separate role/process/evidence | B | VERIFIED | `team_trust.py`, Team runner stage records | Fresh audit remediation + regressions PASS |
| EC-003 / AUD-03 | Process count is derived, not proof | B | VERIFIED | stage-chain identities; integer input rejected | Fresh audit + adversarial suite PASS |
| EC-004 / AUD-04 | Fresh audit and seeded defect use evaluator evidence | B | VERIFIED | baseline/final trusted oracle trajectory | Fresh audit remediation + regressions PASS |
| EC-005 / AUD-05 | Finding closure and blockers are strict | B | VERIFIED | role/stage/artifact-bound finding closure | Fresh audit remediation + regressions PASS |
| EC-006 / AUD-06 | Executable scenario fields are consumed | B | VERIFIED | executable assertion bindings + mutation tests | Fresh audit remediation + regressions PASS |
| EC-007 / AUD-07 | Sections exactly reconcile source headings/hashes | B | VERIFIED | `validate_sections` | Adversarial suite PASS |
| EC-008 / AUD-08 | Coverage rows bind acceptance/work/surface/evidence/review | B | VERIFIED | semantic `validate_coverage` checks | Fresh audit remediation + regressions PASS |
| EC-009 / AUD-09 | Blank/fenced completion values fail | C | VERIFIED | completion parser + adversarial tests | Adversarial suite PASS |
| EC-010 / AUD-10 | VERIFIED conflicts with blockers/checks fail | C/B | VERIFIED | completion + Team oracle reconciliation | Adversarial suite PASS |
| EC-011 / AUD-11 | Empty/duplicate/wrong-set complete reports fail | C | VERIFIED | schema-v3 validator adversarial corpus | Adversarial suite PASS |
| EC-012 / AUD-12 | Metadata/provenance/fallback are recomputed | C | VERIFIED | family validation + provenance quality gate | Fresh audit remediation + regressions PASS |
| EC-013 / AUD-13 | JSON Schema and stdlib structural contract agree | C | VERIFIED | JSON subset validator/equivalence mutations | Adversarial suite PASS |
| EC-014 / AUD-14 | Bool/NaN/Inf/bad budgets fail | C/D | VERIFIED | `harness_core.py` numeric limits | Adversarial suite PASS |
| EC-015 / AUD-15 | Mode abort is exact boolean | C | VERIFIED | mode scorer negative corpus | Adversarial suite PASS |
| EC-016 / AUD-16 | Structured rationale is separately measured | C | VERIFIED | rationale fields/completeness metric | Adversarial suite PASS |
| EC-017 / AUD-17 | Malformed/conflicting events fail controlled | C/D | VERIFIED | shared JSONL parser tests | Adversarial suite PASS |
| EC-018 / AUD-18 | Measurement and quality gate are distinct | D | VERIFIED | schema fields, `--require-gate`, AST regression | Adversarial suite PASS |
| EC-019 / AUD-19 | Unknown post-invocation cost consumes reserve | D | VERIFIED | shared cost accounting + runner paths | Adversarial suite PASS |
| EC-020 / AUD-20 | HEAD/index/scope/oracle integrity fail closed | A | VERIFIED | `ScopeManifest`, Git inventory, oracle hashes | Adversarial suite PASS |
| EC-021 / AUD-21 | Four model cells remain independent | J | NOT_RUN | concrete non-executable run manifest | Paid live calls not authorized |
| EC-022 / AUD-22 | Formal/long-horizon natural activation is measured | J | NOT_RUN | targeted dataset/harness prepared | Paid live calls not authorized |
| EC-023 / AUD-23 | Seven elapsed days precede L5 claim | J | NOT_RUN | `docs/longitudinal-protocol.md` | Seven-day field run not started |
| EC-024 / AUD-24 | Resume corruption/drift/wrong identity fail | F | VERIFIED | resume/state adversarial tests | Adversarial suite PASS |
| EC-025 / AUD-25 | Risk transition follows actual source discovery | G | VERIFIED | executable source fixture evaluator | Deterministic fixture PASS |
| EC-026 / AUD-26 | Ownership conflict/stop/integration are observed | G | VERIFIED | event log + executable integration oracle | Deterministic fixture PASS; live agents separate |
| EC-027 / AUD-27 | Specialist positive/negative/unavailable pairs | G | VERIFIED | source-derived specialist fixture/oracle | Deterministic fixture PASS |
| EC-028 / AUD-28 | TS/PostgreSQL/browser stacks execute genuinely | G | BLOCKED | fixture sources + capability matrix | `tsc`, `psql`, browser unavailable; no full-stack PASS |
| EC-029 / AUD-29 | Independent acceptance oracle is protected | A/G | VERIFIED | external hashed oracle for Core/Team/injection | Fresh audit + adversarial suite PASS |
| EC-030 / AUD-30 | Samples/repetitions/Wilson/stops are frozen | J | VERIFIED | manifest + `sampling.py` tests | Protocol PASS; live samples NOT_RUN |
| EC-031 / AUD-31 | Sanitized re-reviewable evidence bundle exists | I | VERIFIED | regenerated bundle + SHA256 manifest | Final local command bundle PASS |
| EC-032 / AUD-32 | Independent QA has operational protocol | E/B | VERIFIED | runtime policy + stage authority | Fresh Team audit PASS after remediation |
| EC-033 / AUD-33 | Reviewer fix requires new independent key | E/B | VERIFIED | reviewer2 candidate-hash rule/tests | Adversarial suite PASS |
| EC-034 / AUD-34 | Evidence binds source/spec/environment/output | F | VERIFIED | executable evidence schema/freshness | Adversarial suite PASS |
| EC-035 / AUD-35 | State is versioned, atomic, CAS/recoverable | F | VERIFIED | atomic writer, backup recovery tests | Adversarial suite PASS |
| EC-036 / AUD-36 | Dependencies/cycles/stable IDs validate | F | VERIFIED | graph + selective stale closure tests | Adversarial suite PASS |
| EC-037 / AUD-37 | One-writer transfer requires stop/isolation | F | VERIFIED | owner claim/transfer tests | Adversarial suite PASS |
| EC-038 / AUD-38 | Untrusted instructions cannot become authority | E/G | VERIFIED | evaluator-owned action log + mandatory external oracle | Fresh audit remediation + regressions PASS |
| EC-039 / AUD-39 | Missing specialist yields equivalence or BLOCKED | E/G | VERIFIED | policy + source-derived unavailable case | Deterministic fixture PASS |
| EC-040 / AUD-40 | Formal work has budgets/progress stop rules | E/D | VERIFIED | Team policy + strict run limits/reservations | Adversarial suite PASS |
| EC-041 / AUD-41 | Branch protection prepared/applied separated | H | VERIFIED | `docs/governance.md` separates prepared from observed state | NOT_APPLIED; settings mutation not authorized |
| EC-042 / AUD-42 | Version/changelog/fixed target exist | H | VERIFIED | `VERSION`, `CHANGELOG.md`, explicit installer ref | Tag/release not published |
| EC-043 / AUD-43 | Install/update/no-op/drift/rollback safe | H | VERIFIED | installer + provenance/failure-injection tests | Fresh audit remediation + regressions PASS |
| EC-044 / AUD-44 | Actions use verified immutable SHAs | H | VERIFIED | official remote SHAs in workflow | Repository validator PASS |
| EC-045 / AUD-45 | CI validation is structural/behavioral | H | VERIFIED | workflow parser + mutation tests | Repository mutation suite PASS |
| EC-046 / AUD-46 | Common redaction and candidate-tree scan | D | VERIFIED | shared redaction/scanner + synthetic tests | Adversarial suite PASS; not full DLP |
| EC-047 / AUD-47 | CLI version/flags preflight is non-billable | D | VERIFIED | shared preflight in all live runners | Adversarial suite PASS |
| EC-048 / AUD-48 | Source URL/commit/date provenance recorded | I | VERIFIED | refreshed source-synthesis table | Safety Net/DCG upstream remains explicitly UNVERIFIED |
| EC-049 / AUD-49 | README/current/history are separated | I | VERIFIED | concise README, canonical status, history banners | Repository validator PASS |
| EC-050 / AUD-50 | Governance/community files are real | H/I | VERIFIED | SECURITY, CONTRIBUTING, CODEOWNERS, PR template | Repository validator PASS |

## Execution record

| Work unit | Implementation | Independent key | Gate | Notes |
|---|---|---|---|---|
| BASELINE | PASS | n/a | PASS | Required baseline commands passed on clean baseline. |
| A | PASS | PASS | PASS | External oracle/scope negative and positive controls passed. |
| B | PASS | PASS | PASS | Fresh adversarial audit findings were fixed; Team regressions passed. |
| C | PASS | PASS | PASS | Strict completion/schema/event/provenance corpus passed. |
| D | PASS | PASS | PASS | Shared accounting, redaction, preflight, and gate tests passed. |
| E | PASS | PASS | PASS | Authority/specialist/injection boundaries passed deterministic probes. |
| F | PASS | PASS | PASS | Freshness, CAS, recovery, graph, and ownership tests passed. |
| G | PARTIAL | PASS | BLOCKED | Deterministic cells pass; TypeScript/PostgreSQL/browser capabilities unavailable. |
| H | PASS | PASS | PASS | Local distribution/governance preparation passed; settings/publication not applied. |
| I | PASS | PASS | PASS | Canonical status and regenerated sanitized evidence bundle reconcile. |
| J | PREPARED | PASS | NOT_RUN | Manifest/protocol validated; paid live and seven-day runs remain unauthorized/unperformed. |
| FINAL | PASS | PASS | PASS | Local scope only; external cells remain explicitly separated below. |

## Delivery-state separation

| Claim | Status |
|---|---|
| ENGINEERING_HARDENING | LOCALLY_VERIFIED_WITH_BLOCKED_EXTERNAL_CELLS |
| REPOSITORY_GOVERNANCE | NOT_APPLIED |
| LIVE_MODEL_MATRIX | NOT_RUN |
| LONGITUDINAL_FIELD | NOT_RUN |
| PUBLICATION | NOT_AUTHORIZED |
