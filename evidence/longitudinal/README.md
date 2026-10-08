# Longitudinal field ledger

The active seven-day L5 run is recorded in `current-run.json`. It starts only after the deterministic candidate is frozen and contains no backdated samples. Real tasks are appended without deleting failures; private source, secrets, and raw transcripts are excluded. A runtime-policy change starts a new candidate partition or restarts the window.

`IN_PROGRESS` is the only valid state until at least seven actual elapsed days have passed and an independent final analysis has reconciled the ledger.
