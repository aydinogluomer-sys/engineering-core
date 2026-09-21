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

## Sealed activation and Formal Spec Team Mode — 2026-09-20

The description was frozen at baseline commit `953962f2228f4f962bfc9aadddbb9fa0cae4b735` with SHA-256 `f7a652e5c1819319c305a8e06185b8f6bbceb03f5c790f44b4307d09bf1c1bc4` before the holdout was opened. Dataset version `2026-09-20.1` contains 32 positive, 22 negative, and 12 ambiguous cases. Claude Code was `2.1.272` on Windows. Tier A alone controls the confusion matrix; Tier B and Tier C were zero in these runs and did not inflate confirmed activation.

| Model alias | Dataset | Scored positive | Blocked positive | TP | FP | TN | FN | Precision | Recall | Recorded cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `sonnet` | sealed holdout | 32 | 0 | 27 | 0 | 22 | 5 | 1.0000 | 0.8438 | `$4.335969` |
| `haiku` | sealed holdout | 29 | 3 | 5 | 0 | 22 | 24 | 1.0000 | 0.1724 | `$3.555201` |
| `sonnet` | representative holdout, 3 repetitions each | 3 positive / 3 negative | 0 | 3 | 0 | 3 | 0 | 1.0000 | 1.0000 | `$0.559815` |

For Sonnet, database, security, RLS/permissions, and billing/idempotency each achieved 2/2 Tier-A activation. Formal-spec was 0/2, long-horizon 0/1, frontend 1/2, and refactor 1/2; these are retained weaknesses despite the aggregate gate passing. The repeated Sonnet probe selected one security positive (`hp13`), one negative (`hn01`), and one ambiguous case (`ha01`): activation rates were 3/3, 0/3, and 0/3 respectively.

Haiku did not meet the recall gate. One database case timed out; one billing case and one hardening case invoked the skill but ended with CLI/model failure, so all three are `BLOCKED`, not forced into TP/FN. Among scored Haiku positives, only debugging reached 2/2; most high-consequence categories were 0. The holdout was not used to revise the description.

### Formal Spec Team Mode

Every scenario used a disposable Git repository, explicit `/engineering-core`, project-only settings, strict empty MCP configuration, bounded cost/time, no automatic retry, independent fixture tests, protected hashes, and Git index/HEAD checks. Raw reports are redacted and Git-ignored.

| Scenario | Model | Final recorded status | Processes | Cost | Key evidence / limitation |
|---|---|---|---:|---:|---|
| Large specification | `sonnet` | PASS | 3 | `$0.947329` | 18 requirements / five phases reconciled; dirty file, locks, deferral, unrelated failure, seeded cross-module defect, independent QA, and fresh release audit all passed machine scoring. |
| Requirement change | `sonnet` | PASS | 1 | `$0.221538` | Phase A remained VERIFIED; only REQ-003/004/005 were invalidated; retry behavior and current fixture evidence passed machine scoring. |
| Cross-session resume | `sonnet` | PASS | 2 | `$0.276508` | Fresh Session B revalidated repository state, detected drift, marked prior evidence stale, implemented Phase B, and reran integration successfully. |
| Two-Key closure | `sonnet` | PASS | 2 | `$0.324171` | Builder stopped at IMPLEMENTED; independent QA verified negative paths, closed the seeded finding as `VERIFIED_FIXED`, and supplied the second phase key. |
| Fresh release auditor | `sonnet` | PASS | 1 | `$0.176946` | Fresh auditor caught and corrected the seeded producer/consumer schema mismatch before `RELEASE_VERIFIED`; independent contract test passed. |

Earlier Two-Key attempts (`$0.307547`, `$0.315626`, and `$0.229088`) remain retained as FAIL: the first two exposed overly narrow transition scoring, while the third lacked the required verified-finding/transition evidence. Earlier requirement-change/cross-session failures (`$0.150897`, `$0.320563`, `$0.140508`, `$0.346663`, `$0.278680`, and `$0.286095`) exposed structured-evidence alias assumptions before the final PASS runs. Mutation tests were added and the artifact prompts were clarified rather than rewriting historical statuses or tuning runtime policy to a scorer defect.

All five Team Mode scenarios now have a final machine-scored PASS while their failed history remains visible. Together with the primary-model activation and static/hosted evidence, this satisfies the contract's 9.7 evidence gate. It does not establish 9.8 or L5 reliability: Haiku natural recall remains weak, and the full Team suite has not been reproduced across multiple strong coding models or a longitudinal workload.

## Cross-model reliability v3 infrastructure — 2026-09-21

The v3 harness layer adds a four-role model registry, standardized schema, requested/effective-model provenance, fallback ambiguity, canonical failure classes, role-aware activation gates, per-prompt repetition rates, a separate five-prompt formal/long-horizon corpus, a ten-case mode-selection scorer, Team repetition summaries, and explicit total budgets. The frozen runtime description and sealed holdout are unchanged.

No new live model run is claimed by this infrastructure entry. Mode selection is `NOT_RUN` for all four models; Opus/Fable activation, core, Team, and repeatability are `NOT_RUN`; Sonnet core remains `NOT_RUN`. The 9.8 gate is therefore `NOT_VERIFIED`. A full first-pass matrix can consume material model budget before repetitions, so live execution requires an explicit bounded spend decision. Static/unit success must not be cited as cross-model behavior.

See [`cross-model-reliability.md`](cross-model-reliability.md) for the current per-model divergence and limitations.
