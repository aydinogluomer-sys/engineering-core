# Export Reliability Program

## Decision Locks

- LOCK-001: Keep the public `export_record()` call signature unchanged.
- LOCK-002: Do not add dependencies or provider integrations.

## Phase A — normalization

- REQ-001: Normalize account names by trimming and case-folding.
- REQ-002: Reject empty normalized account names.
- REQ-003: Preserve the public account function signature.
- REQ-004: Add positive and empty-input tests.

## Phase B — tenant boundary

- REQ-005: Export reads require matching tenant identity.
- REQ-006: Cross-tenant reads raise `PermissionError` without payload leakage.
- REQ-007: Same-tenant reads retain their current return shape.
- REQ-008: Add positive and forbidden-path tests. This phase is High risk.

## Phase C — replay-safe events

- REQ-009: Duplicate event IDs are applied once.
- REQ-010: Different event IDs remain independent.
- REQ-011: Invalid negative amounts are rejected.
- REQ-012: Add replay and invalid-input tests.

## Phase D — presentation and integration

- REQ-013: Render export labels from normalized account and payload.
- REQ-014: Missing payload renders an explicit unavailable state.
- REQ-015: Integrate tenant-safe export output into the label path.

## Phase E — release closure

- REQ-016: Preserve dirty `notes.txt` exactly.
- REQ-017: Record independent QA evidence and resolve its findings.
- REQ-018: A fresh release auditor must catch or verify correction of the seeded cross-module `EXPORT_SCHEMA_VERSION` mismatch.

## Deferral

- Provider delivery integration is explicitly deferred.

## Release gate

All phases require current evidence. Phase verification is distinct from release verification. The release may be `RELEASE_VERIFIED` only after requirement coverage, Decision Locks, findings, tests, dirty-file preservation, and the schema-version invariant are audited.
