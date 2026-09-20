# Deterministic Enforcement Integration

`engineering-core` is behavioral engineering policy. It can tell Claude how to classify risk, preserve scope, verify work, and stop at safety boundaries, but prompt text cannot make unsafe actions impossible.

Deterministic prevention belongs to controls outside the skill. Observability makes execution visible. Codebase-intelligence providers supply optional context. These layers cooperate but are not interchangeable.

## Control options

Choose controls according to the deployment and threat model:

| Control | Useful role | Important limit |
|---|---|---|
| Claude Code permissions | Tool/action allow, deny, or ask boundaries | Coverage depends on configured tools and invocation paths |
| OS/container sandbox | Filesystem, process, and network containment | Must be correctly scoped and maintained |
| Managed/organization policy | Centrally governed restrictions | May not express repository-specific semantic rules |
| `PreToolUse` hooks | Inspect or reject supported tool calls before execution | Parser, platform, timeout, and bypass coverage require testing |
| Safety Net / DCG-style controls | Classify high-risk command intent and gate it | Heuristics can produce false positives and false negatives |
| Provider-side controls | Protect deploy, database, billing, or credential APIs | Covers only the provider/action actually governed |

No control is installed or enabled by this repository. Project owners decide enforcement policy and failure posture.

## Consequential action families

Threat-model at least:

- Git history/worktree operations such as reset, clean, force push, branch deletion, and history rewriting;
- recursive filesystem deletion, wildcards, broad moves, permission changes, and overwrites;
- database drop, truncate, destructive migration, bulk mutation, and production connection targeting;
- production deploy, rollback, infrastructure mutation, release publication, and secret/credential operations;
- billing, messaging, identity-provider, storage, and other externally visible side effects.

Target resolution matters. A command that is safe in a disposable fixture may be catastrophic against a workspace root or production account.

## Why substring blocking is insufficient

Naive matching such as “deny any command containing `rm`” both blocks benign text and misses indirect execution. Real coverage must account for shell aliases/functions, PowerShell pipelines, Python or other interpreter wrappers, `xargs`/`find`, encoded payloads, SQL embedded in scripts, package scripts, environment expansion, command composition, and provider calls hidden behind helper programs.

Avoid claiming complete coverage. Maintain explicit benign, destructive, wrapped/indirect, platform-specific, and ambiguous fixtures. Measure both false positives and false negatives.

## Failure design

Define behavior for each supported event and outcome:

- allow, deny, or ask;
- parse failure or unsupported syntax;
- hook timeout, crash, or unavailable runtime;
- unsupported operating system or shell;
- logging/telemetry failure;
- secret-bearing inputs and required redaction;
- audit-record retention and access.

There is no universal fail-open or fail-closed answer. A read-only formatting helper and a production database mutation have different consequences. Choose per action class, document the tradeoff, and ensure failures cannot silently masquerade as successful enforcement.

## Evaluation fixtures

Before deployment, test categories rather than a few favored strings:

1. known-benign commands that must remain usable;
2. direct destructive commands and dangerous target variants;
3. wrapped, aliased, piped, encoded, scripted, and provider-indirect forms;
4. Windows PowerShell/cmd and POSIX shell variants actually supported;
5. expected false-positive boundaries and known unsupported forms;
6. timeouts, malformed hook input, hook crashes, and missing dependencies;
7. logs containing secret-shaped values to confirm redaction.

Re-run fixtures whenever command parsing, shell support, hook runtime, permissions, or provider interfaces change. Observability can report decisions and failures, but it does not prove enforcement correctness.
