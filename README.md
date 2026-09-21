engineering-core




Risk-adaptive engineering operating policy for Claude Code.

engineering-core gives Claude Code a reusable software-engineering discipline for implementation, debugging, refactoring, removal, testing, review, migration, and release work.

It does not force every task through the same heavyweight workflow. It scales investigation, planning, safety, testing, review, and coordination to the actual consequence and uncertainty of the change.

Core principle

Use the minimum engineering ceremony required by the risk of the task, and require stronger evidence as consequence increases.

A typo should remain a tiny task.

A one-line authorization, billing, database, or production change should not be treated as low risk merely because the diff is small.

Why engineering-core exists

Coding agents commonly fail in two opposite directions:

Failure mode

Typical behavior

Cost

Under-engineering

Rushes into consequential edits with thin evidence

Broken auth, billing, data, migrations, or production behavior

Over-engineering

Turns a local, reversible fix into plans, ledgers, agents, and broad test suites

Wasted context, latency, money, and attention

engineering-core rejects both.

LOW RISK                                           HIGH / CRITICAL RISK
────────                                           ────────────────────
local · reversible                                auth · billing · data
known precedent                                   schema · production
narrow proof                                      shared contracts
no hard-floor surface                             irreversible side effects
        │                                                  │
        ▼                                                  ▼
Adaptive Fast-Exit                               Expanded lifecycle
minimal inspection                               deeper investigation
minimum correct edit                             explicit invariants
focused verification                             negative paths
final diff review                                specialist / independent review
compact completion                               release gates

Ceremony follows risk, not diff size.

What it provides

The universal operating loop is:

CLASSIFY
   ↓
DISCOVER
   ↓
INVESTIGATE
   ↓
PLAN
   ↓
IMPLEMENT
   ↓
VERIFY
   ↓
REVIEW
   ↓
COMPLETE

Backward transitions are first-class:

new evidence changes risk      → CLASSIFY
understanding is insufficient  → INVESTIGATE
architecture does not fit      → PLAN / INVESTIGATE
verification fails             → classify failure → IMPLEMENT / INVESTIGATE
review finds a defect          → IMPLEMENT → VERIFY → REVIEW
requirements change            → invalidate affected evidence → replan impacted path
authority is missing           → WAIT_FOR_AUTHORIZATION

For genuinely low-risk work, investigation and planning compress into Adaptive Fast-Exit. For higher-risk work, the same lifecycle expands rather than being replaced by a separate methodology.

Key behaviors include:

risk-adaptive workflow selection;

repository instruction and authority discovery;

evidence-first, bounded codebase investigation;

minimum-correct implementation and scope control;

systematic root-cause debugging;

repeated-failure and loop classification;

risk-adaptive positive and negative verification;

database, auth, authorization, billing, secret, and production escalation;

Git/user-work preservation;

bounded subagent delegation;

formal specification and implementation.md execution;

requirement traceability and resumable long-horizon state;

independent QA and fresh release audit when warranted;

removal/completeness audits;

optional code-intelligence integrations with native fallbacks;

evidence-based completion semantics.

Architecture: four responsibilities, deliberately separated

engineering-core is strongest when behavioral policy is not confused with deterministic enforcement or tooling.

┌──────────────────────────────────────────────────────────────────────┐
│ 1 — ENGINEERING POLICY                                               │
│ engineering-core                                                     │
│ classify · investigate · plan · implement · verify · review · close │
│                                                                      │
│ Behavioral policy. Does not itself block shell commands or grant     │
│ permissions.                                                         │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │ may cooperate with
                  ┌────────────────┼────────────────┐
                  ▼                ▼                ▼
┌──────────────────────┐ ┌───────────────────┐ ┌──────────────────────┐
│ 2 — CONTROL PLANE    │ │ 3 — OBSERVABILITY│ │ 4 — CODE INTELLIGENCE│
│ optional             │ │ optional          │ │ optional              │
│ permissions          │ │ session traces    │ │ code graphs           │
│ sandbox              │ │ agent/tool views  │ │ LSP / indexes         │
│ hooks / guards       │ │ telemetry         │ │ dependency maps       │
│ allow/deny/ask       │ │ visibility only   │ │ discovery leads       │
└──────────┬───────────┘ └─────────┬─────────┘ └──────────┬───────────┘
           │                       │                       │
           └───────────────────────┼───────────────────────┘
                                   ▼
                 ┌──────────────────────────────────┐
                 │ REPOSITORY + RUNTIME EVIDENCE    │
                 │ source · tests · config · schema │
                 │ history · logs · actual behavior │
                 └──────────────────────────────────┘

Layer

Responsibility

Required?

Engineering policy

Risk, evidence, scope, implementation discipline, verification, completion

Yes

Control plane

Deterministic allow / deny / ask / sandbox / guard behavior

No

Observability

Visibility into agents, tools, sessions, and traces

No

Code intelligence

Faster symbol, relationship, dependency, and repository discovery

No

Two boundaries are non-negotiable:

Visibility is not correctness.

Generated graphs and indexes are leads, not authority, until grounded in source, tests, config, schema, history, or runtime evidence.

Risk model

Risk is classified from consequence, not line count or file count.

                       RISK DIMENSIONS
        ┌──────────────┬───────────────┬──────────────┐
        │ consequence  │ reversibility │ uncertainty  │
        ├──────────────┼───────────────┼──────────────┤
        │ blast radius │ privilege     │ data         │
        ├──────────────┼───────────────┼──────────────┤
        │ side effects │ verification difficulty      │
        └──────────────┴──────────────────────────────┘
                              │
                              ▼
              highest applicable dimension controls
                              │
                              ▼
             Low ── Moderate ── High ── Critical

Hard floors

Some surfaces cannot be classified below a minimum risk merely because the patch is small.

Surface

Minimum risk

Authorization / RLS / tenant isolation boundary

High

Billing / payments / credits / money-path webhook

High

Production-data schema migration or lock-sensitive migration

High

Shared public / published API contract

High

Production mutation / irreversible external action

Critical

Credential exposure / secret leakage event

Critical

Downward reclassification requires positive evidence.

Three runtime modes

The dispatcher selects exactly one starting mode from consequence, uncertainty, specification depth, and coordination need.

                         ┌─────────────────────┐
                         │   MODE DISPATCHER   │
                         └──────────┬──────────┘
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
      ┌──────────────────┐ ┌──────────────────┐ ┌────────────────────┐
      │ Adaptive         │ │ Standard         │ │ Formal Spec        │
      │ Fast-Exit        │ │ Engineering      │ │ Team Mode          │
      ├──────────────────┤ ├──────────────────┤ ├────────────────────┤
      │ Low only         │ │ default mode     │ │ multi-phase /      │
      │ local            │ │ ordinary work    │ │ long-horizon       │
      │ reversible       │ │ proportional     │ │ requirement ledger │
      │ known precedent  │ │ lifecycle        │ │ independent QA     │
      │ narrow proof     │ │                  │ │ Two-Key closure    │
      └──────────────────┘ └──────────────────┘ │ fresh release audit│
                                                └────────────────────┘

Adaptive Fast-Exit

Use only when all of the following are evidenced:

Low risk;

local and reversible behavior;

unambiguous one-sentence contract;

known local precedent or trivial pattern;

narrow focused proof;

no hard-floor surface;

no consequential auth, billing, schema, production, concurrency, shared-contract, secret, or external-side-effect boundary.

Fast-Exit aborts as soon as those assumptions stop being true.

Standard Engineering Mode

Default for ordinary implementation, debugging, refactoring, migration, review, removal, and test/build work.

It applies the universal lifecycle proportionally without forcing multi-agent orchestration.

Formal Spec Team Mode

Use for qualifying large or dependency-rich formal work where traceability, independent verification, resumable state, or release closure matter.

A formal file alone does not trigger Team Mode.

See engineering-core/references/formal-spec-team-mode.md.

Formal Spec Team Mode

Team Mode is orchestration discipline, not “use as many agents as possible.”

                   ORIGINAL SPECIFICATION
                    authoritative source
                            │
                            ▼
                  ┌──────────────────────┐
                  │    SPEC COMPILER     │
                  │ section inventory    │
                  │ requirement extract  │
                  │ coverage graph       │
                  └──────────┬───────────┘
                             ▼
                  ┌──────────────────────┐
                  │ REQUIREMENT LEDGER   │
                  │ decision locks       │
                  │ work-unit graph      │
                  └──────────┬───────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     ┌─────────────┐  ┌──────────────┐ ┌───────────────┐
     │ Orchestrator│  │ Writer(s)    │ │ Independent   │
     │ / Tech Lead │  │ bounded work │ │ QA / specialist│
     └──────┬──────┘  └──────┬───────┘ └──────┬────────┘
            └────────────────┼──────────────────┘
                             ▼
                  ┌──────────────────────┐
                  │ TWO-KEY PHASE CLOSE  │
                  │ implementation key   │
                  │ independent key      │
                  └──────────┬───────────┘
                             ▼
                  ┌──────────────────────┐
                  │ FRESH RELEASE AUDIT  │
                  │ RELEASE_VERIFIED     │
                  │ NOT_VERIFIED/BLOCKED │
                  └──────────────────────┘

Two-Key closure

For Moderate / High / Critical Team Mode phases:

Key

Meaning

Implementation key

Intended diff exists, required current tests pass, forbidden scope is absent, builder evidence maps to requirements

Independent key

Independent QA/reviewer acceptance passes, required negative paths pass, required specialist evidence is resolved

If either key is missing, a phase may be IMPLEMENTED but not VERIFIED.

PHASE_VERIFIED and RELEASE_VERIFIED are intentionally different states.

Authority order

Current explicit user instruction

Original formal specification

Applicable repository instructions

Current source / config / test / schema / runtime evidence

Derived requirement and work-unit state

Agent reports

Evidence-first investigation

Consequential claims should be grounded in the strongest available evidence.

STRONGER
───────
current source
current tests
schemas / migrations
configuration
Git status / diff / history
runtime behavior / logs
current authoritative specification

generated maps / graph indexes
tool summaries
README / comments
conversation memory
agent self-reports
───────
WEAKER

Bounded investigation

target symbol
   ↓
nearest test / precedent
   ↓
direct callers / relevant config
   ↓
decision-relevant question still unanswered?
        ├─ yes → expand one hop
        └─ no  → stop expanding

Before broadening the search, ask:

What decision will this additional evidence change?

Optional graph/index tools can accelerate discovery. Their absence is not a blocker.

Implementation and debugging discipline

Minimum-correct implementation

Optimize for the smallest change that completely satisfies the requirement and repository invariants.

Prefer existing local patterns, direct behavior, fitting abstractions, explicit contracts, and narrow scope.

Avoid opportunistic refactors, unrelated cleanup, speculative configurability, unnecessary dependency churn, and broad formatting changes.

Minimum-correct is not minimum line count.

Root-cause debugging

REPRODUCE
   ↓
LOCALIZE
   ↓
HYPOTHESIZE
   ↓
DISCRIMINATE
   ↓
FIX ROOT CAUSE
   ↓
VERIFY

Step

Discipline

Reproduce

Exact failure, inputs, environment, expected vs observed

Localize

Earliest violated invariant, not merely the final symptom

Hypothesize

Falsifiable explanation

Discriminate

Cheapest experiment that separates competing hypotheses

Fix

Smallest correction at the actual broken boundary

Verify

Original repro + regression + relevant negative path

Loop detection

Same action twice without new evidence → change tactic

Third equivalent failure → classify the failure before more edits

Failure classes include implementation defect, test-oracle defect, environment/tooling, dependency/external service, permission, flaky/timing, missing prerequisite, stale artifact, migration/state mismatch, scope conflict, and unknown.

Never test-cheat. Do not hardcode production behavior to fixtures or weaken valid assertions merely to turn CI green.

Verification and completion

Verification depth scales with risk.

Low
→ narrow meaningful check
→ final diff review

Moderate
→ targeted tests
→ relevant static/integration checks
→ affected-module regression
→ final diff review

High
→ invariants
→ negative paths
→ compatibility / concurrency where relevant
→ specialist or independent review
→ broader regression / release gates

Critical
→ all applicable High checks
→ exact action + target authorization
→ consequence review
→ production / external-action gates

A typical verification order is:

syntax/static
→ targeted unit
→ module
→ type/lint
→ integration
→ E2E
→ broader regression

Stale evidence rule

A passing test is evidence only for the code/state it actually tested.

After a relevant final edit, affected evidence becomes stale until rerun or replaced by equivalent current evidence.

Completion states are not synonyms

implemented
   ↓
locally verified
   ↓
phase verified
   ↓
release verified
   ↓
reviewed
   ↓
merged
   ↓
released
   ↓
deployed

A required check that fails or cannot be established without equivalent evidence produces NOT_VERIFIED or BLOCKED—never a contradictory “complete but unverified.”

Execution Summary contract

Every substantive execution ends with:

### Execution Summary
- **Policy:** engineering-core
- **Risk:** Low | Moderate | High | Critical
- **Status:** NO_CHANGE | IMPLEMENTED | VERIFIED | NOT_VERIFIED | BLOCKED
- **Changed:** …
- **Verified:** …
- **Limitations:** … | None

Safety and authorization

Trust-boundary review deepens when a change crosses:

input
→ identity
→ authorization
→ data
→ side effect
→ failure / recovery

Common triggers include authentication and authorization, RLS/tenant isolation, sessions/tokens, secrets/PII, billing/payments/webhooks, uploads, SQL construction, infrastructure privileges, CI secrets, cryptography, and production actions.

Safety profiles

Profile

Focus

Database / migration

Ordering, locks, backfill, RLS, grants, forward-only vs rollback, production rows

Auth / authorization

Server-side enforcement, default-deny, tenant isolation, admin bypass

Billing / side effects

Idempotency, retries, replay, partial completion, reconciliation, auditability

Git / user work

Preserve unknown user-owned changes; no broad reset/clean/force without exact authority

Secrets

Never print, commit, prompt, or log secrets; treat exposure as a separate consequential event

Destructive / production

Exact action + exact target authorization after required gates

Authorization is action-and-target specific.

Exact current authorization for the exact action and target is sufficient after required gates; do not ask redundantly.

Broad, implied, stale, ambiguous, or differently scoped intent is not authority.

“Prepare this for production” does not authorize deployment.

“Deploy this exact release to production after the required checks pass” does.

Honest safety boundary

engineering-core is a behavioral policy. It does not claim deterministic prevention of unsafe actions.

Deterministic blocking belongs to permissions, sandboxing, managed policy, and optional hooks/command guards. See docs/deterministic-enforcement.md.

Progressive disclosure

SKILL.md is a runtime dispatcher, not a monolithic handbook.

                    ┌───────────────────┐
                    │     SKILL.md      │
                    │ universal loop    │
                    │ invariants        │
                    │ Fast-Exit         │
                    │ mode routing      │
                    │ safety boundary   │
                    │ completion        │
                    └─────────┬─────────┘
                              │ load only when needed
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌────────────┐
       │ references │   │ examples   │   │ scripts    │
       │ deep policy│   │ concrete   │   │ validation │
       │ procedures │   │ scenarios  │   │ tooling    │
       └────────────┘   └────────────┘   └────────────┘

At current main, the distributable runtime package contains 19 files and the SKILL.md entrypoint is 83 lines.

Package structure

.
├── README.md
├── LICENSE
├── .gitignore
├── implementation.md
├── .github/
│   └── workflows/
│       └── validate.yml
├── docs/
│   ├── claude-router.md
│   ├── deterministic-enforcement.md
│   └── l4-evaluation.md
├── evals/
│   ├── README.md
│   ├── activation/
│   ├── formal-spec-team/
│   ├── scenarios/
│   ├── completion_summary.py
│   ├── run_l4_eval.py
│   ├── test_completion_summary.py
│   └── test_l4_eval.py
├── scripts/
│   └── validate_repository.py
└── engineering-core/
    ├── SKILL.md
    ├── examples/
    │   ├── small-fix.md
    │   ├── fast-exit-abort.md
    │   ├── normal-feature.md
    │   ├── high-risk-change.md
    │   ├── removal-task.md
    │   └── large-spec-execution.md
    ├── references/
    │   ├── operating-model.md
    │   ├── formal-spec-team-mode.md
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

Installation

Personal skill

git clone https://github.com/aydinogluomer-sys/engineering-core.git

macOS / Linux:

mkdir -p ~/.claude/skills
cp -R engineering-core/engineering-core ~/.claude/skills/engineering-core

PowerShell:

New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse ".\engineering-core\engineering-core" "$HOME\.claude\skills\engineering-core"

Restart Claude Code if necessary.

Project-scoped skill

Copy the inner engineering-core/ directory to:

<project>/.claude/skills/engineering-core/

The installed directory should contain:

SKILL.md
examples/
references/
scripts/

Usage

Typical requests:

Fix this race condition.
Implement this feature.
Remove this subsystem completely.
Review and fix this authorization flow.
Implement this implementation.md phase by phase.
Prepare this branch for release.

Explicit invocation:

/engineering-core

engineering-core does not replace specialist domain skills. It supplies the cross-cutting operating policy:

risk
+ evidence
+ scope
+ implementation discipline
+ verification
+ review
+ completion semantics

Optional routing and integrations

Project routing

For stronger project-level guidance so Claude consistently considers engineering-core for substantive engineering work, see docs/claude-router.md.

The router is optional and is not deterministic enforcement.

Natural skill selection is measured separately from explicit /engineering-core invocation.

Code intelligence

When already available or explicitly requested, the core can cooperate with CodeGraph, Cartographer, Graphify, language servers, or repository indexes.

These are context providers, not sources of truth. Native search/read/Git fallback remains valid.

Deterministic enforcement

Permissions, sandboxes, hooks, and command guards belong to a separate control plane.

See docs/deterministic-enforcement.md.

Validation model: L1–L5

L5  Longitudinal real-world field evidence
▲
L4  Live Claude Code behavioral evaluation
▲
L3  Manual / adversarial scenario evaluation
▲
L2  Policy lint / static policy properties
▲
L1  Structural validation

Level

What it establishes

What it does not establish

L1

Package tree, links, frontmatter, structural constraints

Runtime model behavior

L2

Statically observable policy properties

Correct live engineering decisions

L3

Adversarial reasoning/scenario coverage

Longitudinal reliability

L4

Observed Claude Code behavior in disposable repositories

Universal behavior or field reliability

L5

Longitudinal real-world evidence

—

A lower level never claims a higher-level guarantee.

Validate the package

Python 3.10+:

python engineering-core/scripts/validate_skill.py engineering-core
python engineering-core/scripts/test_validate_skill.py
python evals/test_completion_summary.py
python evals/test_l4_eval.py
python evals/activation/test_activation_eval.py
python evals/formal-spec-team/test_team_eval.py
python -m py_compile \
  engineering-core/scripts/validate_skill.py \
  engineering-core/scripts/test_validate_skill.py \
  scripts/validate_repository.py \
  evals/completion_summary.py \
  evals/test_completion_summary.py \
  evals/run_l4_eval.py \
  evals/test_l4_eval.py \
  evals/activation/run_activation_eval.py \
  evals/activation/test_activation_eval.py \
  evals/formal-spec-team/run_team_eval.py \
  evals/formal-spec-team/test_team_eval.py
python scripts/validate_repository.py .

Hosted static CI runs on Linux and Windows with Python 3.10 and 3.14.

A green static validator does not prove correct root-cause discovery, safe Critical handling, natural activation, or absence of scope creep.

Live behavioral evaluation

L4 evaluation is intentionally local/manual because it invokes Claude Code and has time/cost implications.

Each case uses a disposable Git repository and separate Claude process. PASS requires machine-scored artifact, Git, and independent-test evidence; zero process exit or a model-written VERIFIED claim is not sufficient.

Core explicit-activation smoke

python evals/run_l4_eval.py --case small --model haiku --per-case-budget 0.35 --total-budget 0.35

Natural activation

python evals/activation/run_activation_eval.py \
  --dataset holdout \
  --mode natural \
  --description current \
  --model sonnet \
  --per-case-budget 0.30 \
  --total-budget 19.80

Formal Spec Team Mode

python evals/formal-spec-team/run_team_eval.py --case two-key-closure --model haiku
python evals/formal-spec-team/run_team_eval.py --model sonnet --per-process-budget 1.00

See evals/README.md, evals/activation/README.md, evals/formal-spec-team/README.md, and docs/l4-evaluation.md.

Current evidence status

Evidence is reported conservatively and historically; failures are retained rather than rewritten.

Hosted validation

Current main has a successful hosted Validate workflow.

L4 core behavior

The six explicit-activation core families have final recorded PASS cases:

small task;

moderate feature;

authorization boundary;

dirty worktree;

missing graph provider;

formal specification.

These are bounded examples, not universal compliance rates.

Natural activation — sealed holdout, 2026-09-20

Model

Scored positive

Blocked positive

TP

FP

TN

FN

Precision

Recall

Sonnet

32

0

27

0

22

5

1.0000

0.8438

Haiku

29

3

5

0

22

24

1.0000

0.1724

Twelve ambiguous prompts were reported separately and excluded from the binary confusion matrix.

These are model-specific observations, not routing guarantees.

Formal Spec Team Mode — 2026-09-20

Final machine-scored PASS exists for all five maintained scenarios:

large specification;

requirement change;

cross-session resume;

Two-Key closure;

fresh release auditor.

Historical failed attempts remain in the evidence record.

L5

Not established.

The project does not claim longitudinal real-world reliability from static validation or bounded L4 runs.

See docs/l4-evaluation.md.

What engineering-core is not

Not this

What engineering-core actually is

Deterministic security sandbox

Behavioral engineering policy

Destructive-command blocker

Defines when exact authority is required

Replacement for permissions/hooks

Compatible with them; does not silently install them

Mandatory multi-agent framework

Conditional Team Mode with bounded roles

Code graph

Can use graph/index providers as optional discovery aids

Security scanner

Escalates security-sensitive work to stronger review

Domain framework

Cross-cutting engineering discipline

Plan-file requirement for every task

Fast-Exit intentionally skips heavyweight artifacts

“Tests passed = safe” claim

Evidence model that distinguishes what each check proves

Design influences

The design synthesizes—rather than concatenates—principles from:

official Claude Code guidance;

Superpowers;

gstack;

Trail of Bits skills;

Safety Net / Destructive Command Guard concepts;

Claude Code Hooks Mastery;

Multi-Agent Observability;

CodeGraph;

Cartographer;

Graphify;

ClaudeKit;

Alireza Claude Skills.

The project intentionally rejects:

mandatory heavyweight planning for every task;

mandatory multi-agent execution;

mandatory TDD regardless of task type;

mandatory graph/index tooling;

automatic hook or MCP installation;

treating observability as correctness;

duplicating specialist domains inside the core;

a monolithic SKILL.md;

static-validator claims about runtime behavior.

See engineering-core/references/source-synthesis.md.

Design thesis

engineering-core is not trying to be the best debugger, security scanner, code graph, test framework, or release system in isolation.

Its purpose is to provide one coherent engineering control policy across all of them:

risk-adaptive workflow
+ evidence-first context
+ minimum-correct implementation
+ systematic debugging
+ targeted verification
+ security escalation
+ bounded collaboration
+ independent closure where needed
+ honest completion semantics

Move fast when the change is cheap to be wrong about. Become rigorous when it is expensive to be wrong about. Never confuse confidence with evidence.

License

MIT. See LICENSE.
