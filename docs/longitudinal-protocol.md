# Seven-day longitudinal reliability protocol

Status: `IN_PROGRESS`. The current ledger began at `2026-10-08T17:27:27.790565Z` for deterministic candidate `4de42795e3343c0bc0d81a32627ab3dbff17dc1a`. Its earliest possible seven-day completion is `2026-10-15T17:27:27.790565Z`. Seven real elapsed days cannot be compressed; until the time and independent-analysis gates pass, no L5 PASS is claimed.

1. Freeze a separately authorized live-run manifest, repository commit, dataset hashes, model registry, and environment fingerprint.
2. For seven elapsed calendar days, record each eligible real engineering task without selecting only successes. Store task class, risk, chosen mode, mode transitions, loop events, stale-state events, specialist obligations, scope changes, verification, final outcome, effective model, cost, and limitations.
3. Do not store private source, secrets, user content, or raw model transcripts in a publishable bundle. Use hashes and sanitized evidence pointers.
4. Treat interruptions, blocked capabilities, user corrections, and abandoned runs as outcomes rather than deleting them.
5. Keep pilot, confirmatory, and field samples separate. Repetitions do not count as distinct prompts.
6. At day seven, calculate per-category counts and Wilson 95% intervals. Fewer than 20 independent prompts in a critical category is an explicit small-sample limitation.
7. A fresh reviewer reconciles recorded outcomes with source evidence and checks survivorship bias, missing failures, fallback identity, and unsupported `PASS` claims.

No L5 or longitudinal reliability claim is valid until the full elapsed protocol and independent audit complete.

The sanitized active ledger lives in [`../evidence/longitudinal/`](../evidence/longitudinal/). An empty task list means the protocol has started but no qualifying real task has yet been captured; synthetic tasks are not added to inflate the sample.
