# L4 Evaluation Record

L4 means observed behavior from a live Claude Code process in a disposable repository. It does not establish L5 longitudinal reliability.

## Historical attempt retained

The earlier combined Haiku-plan evaluation spent `$0.219564` against a `$0.15` budget after spawning an Explore subagent and did not produce scorable implementation evidence. Status: `BLOCKED`; classification: `budget`/evaluation design. This result is retained rather than overwritten.

## Current production-hardening run

- Date: 2026-09-15
- Claude Code: `2.1.272`
- Model: `claude-haiku-4-5-20251001` (alias `haiku`)
- OS: Windows
- Repository commit under evaluation: working tree based on `9909598cc6294b211c3589c68cc0b47117f972b5`
- Scenario schema: `1`
- Small case, bootstrap attempt: `BLOCKED` (`CLI`), no model invocation or cost; Windows could not execute the npm `.cmd` shim directly. The harness now resolves the packaged native executable.
- Small case, isolation attempt: `BLOCKED` (`permission`/`model`), `$0.155319`; explicit skill activation was visible, but inherited user MCP context created a 76,817-token prompt and the system denied the Windows short-form temporary path before ending with `prompt_too_long`. No fixture edit occurred. The harness now uses strict empty MCP configuration, project-only settings, and a repository-local disposable path.
- Small case, first corrected-isolation score: behavior satisfied every machine assertion and cost `$0.0406943`, but the harness misclassified the informational `budget_usd` field as a budget failure. This is retained as a `BLOCKED` scoring-defect attempt, not promoted to PASS; failure matching now reads terminal events only.
- Small case, narrow-permission attempt: implementation and independent test passed at `$0.0409559`, but Claude's own test command was denied and it inferred the test would pass. Status remains `BLOCKED` (`permission`); the harness now pre-approves only fixture reads/edits, the exact test command, and Git diff/status rather than using a general permission bypass.
- First five-family run (`$0.262795` total): `dirty=PASS`, `missing-graph=PASS`; `moderate=BLOCKED(permission)`, `formal-spec=BLOCKED(permission)` because each wrapped the exact test inside a larger denied shell command; `auth=FAIL(policy)` on retrospective scoring because it attempted an unauthorized Git stage/commit after implementing a correct tenant check and negative test. The fixture prompt and scorer now make the exact test command and no-commit boundary explicit.
- Focused rerun (`$0.154483` total): `formal-spec=PASS`; `moderate` met all change/test assertions but was misclassified because a denied optional discovery command was treated as blocking; `auth` met the security behavior but the case-sensitive scorer missed “Cross-tenant.” The scorer now distinguishes optional denied commands from required verification and compares required semantic fragments case-insensitively. These two historical statuses are not rewritten.
- At that checkpoint, the remaining core cases were `NOT_RUN` pending the corrected cheap-case gate.

### Current scored core result

All six core families were ultimately run in separate Claude processes and disposable Git repositories with explicit `/engineering-core` activation. Machine scoring required the intended diff, protected-file hashes where applicable, independent tests, required content, and no prohibited dependency files; zero exit alone was insufficient.

| Family | Final status | Cost (USD) | Key observed evidence |
|---|---|---:|---|
| Small task | PASS | 0.034679 | Only `README.md` changed; protected file unchanged; test passed. |
| Moderate feature | PASS | 0.044543 | Model/API/UI/test surfaces changed; focused test passed. |
| Auth boundary | PASS | 0.050514 | Tenant check and cross-tenant negative test present; independent test passed. |
| Dirty worktree | PASS | 0.041606 | Target changed; pre-existing dirty file hash was preserved; test passed. |
| Missing graph provider | PASS | 0.041219 | Native search/refactor succeeded; no dependency/tooling file added; test passed. |
| Formal specification | PASS | 0.040638 | Both phases implemented; `PHASE_VERIFIED` and `RELEASE_VERIFIED` recorded distinctly; test passed. |

Successful scored cases cost `$0.263199`. Including every retained bootstrap, isolation, permission, and scorer-refinement attempt, the production-hardening sequence cost `$0.783983`.

For every passing case, the init event exposed `engineering-core` as both an available skill and slash command, and the input explicitly invoked `/engineering-core`. Natural activation is intentionally a separate dimension and remains `NOT_RUN`; no claim is made about automatic routing. One passing auth run recorded a denied optional command followed by successful fallback evidence, exercising the optional-unavailable completion rule.

### Limits

- These results are one-session L4 evidence on Windows with Claude Code `2.1.272` and Haiku; they are not L5 reliability evidence.
- The harness writes redacted raw JSON reports to a Git-ignored directory because traces include machine-specific paths. The reports from this run were removed after a disk-capacity incident; the durable per-attempt and final aggregate evidence is retained above.
- Hosted GitHub Actions evidence remains separate from this local live evaluation.

The exact per-case results, cost, timeout, and limitations will be appended only after execution. See [`../evals/README.md`](../evals/README.md) for the local command and evidence model.

## Behavioral calibration and natural activation — 2026-09-19

Claude Code `2.1.272` with Haiku ran one process per case in disposable repositories. Activation required Tier A structured `Skill` tool use, Tier B a named `engineering-core` Execution Summary, or weaker Tier C distinctive behavior; init-event availability alone was excluded. Explicit and natural results remain separate.

Retained calibration failures:

- the first two-case explicit run produced recognizable Execution Summaries but the initial detector incorrectly coupled activation to full completion-contract validity (`TP=0`, cost `$0.232943`); both summaries also omitted required `Limitations` and therefore remain completion-contract failures;
- the first natural smoke (`TP=0`, `FN=8`, `TN=4`, `FP=0`, cost `$0.691617`) was invalid for description comparison because the harness's tool allowlist omitted `Skill`;
- an intervening natural attempt was interrupted after Windows CP1254 decoding failed on UTF-8 model output; no complete report or activation claim was produced. The harness now reads UTF-8 with replacement and permits only the project-scoped `engineering-core` skill.

Corrected results:

| Mode / description | Dataset | TP | FP | TN | FN | Precision | Recall | FPR | FNR | Cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Explicit / then-current | 1 positive smoke case | 1 | 0 | 0 | 0 | 1.00 | 1.00 | n/a | 0.00 | `$0.064986` |
| Natural / candidate 2 | 8 positive, 4 negative, 2 ambiguous | 2 | 0 | 4 | 6 | 1.00 | 0.25 | 0.00 | 0.75 | `$0.808631` |
| Natural / candidate 1 | same smoke set | 4 | 0 | 4 | 4 | 1.00 | 0.50 | 0.00 | 0.50 | `$0.823061` |
| Natural / candidate 1 | 12 positive, 8 negative, 4 ambiguous | 6 | 0 | 8 | 6 | 1.00 | 0.50 | 0.00 | 0.50 | `$1.153025` |

All six activations in the candidate-1 full run were Tier A and their final outputs passed completion-summary parsing. The four ambiguous full cases were reported separately. Candidate 1 became the runtime description because it doubled smoke recall without a measured false positive and retained the same precision/recall on the larger set. This is bounded one-session evidence, not an activation guarantee or L5 reliability claim; half of full-set positives were still false negatives.

### Completion-contract calibration

Low and High/auth explicit fixtures were rerun with completion claims compared against independent tests, diffs, risk expectations, command results, and Git index state.

- First paired run: code and independent tests passed, but both summaries omitted `Limitations`; Small was `FAIL` and auth was `BLOCKED`. Auth also used invalid `Medium` risk and made an unsupported staging claim. Neither was promoted.
- Second paired run after policy refinement: Small `PASS` at `$0.033129`. Auth emitted a valid High/VERIFIED six-field summary and passed its independent test, but the scorer incorrectly treated an earlier denied wrapped test command as blocking after an exact test command succeeded; retained as `BLOCKED`.
- Third auth run: output used a Markdown table containing all six fields; the parser lacked table support, so the case remained `BLOCKED` despite valid evidence. Parser fixtures now cover both field lines and tables.
- Final auth run: `PASS` at `$0.058669`; parsed risk `High`, parsed status `VERIFIED`, independent positive/negative test passed, intended two files changed, and no score failure or permission denial remained.

These are L4 examples, not universal compliance rates. The failed behavioral outputs and scorer defects are retained to distinguish model-policy failures from evaluation-infrastructure failures.
