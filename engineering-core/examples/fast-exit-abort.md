# Worked Example: Fast-Exit Abort

## Initial classification

Request: “Rename this private formatting helper and update its focused test.”

Initial inspection shows a local helper, a nearby precedent, and one focused test. The one-sentence contract is: rename the private helper without changing output, limited to its module and test, proved by the focused test and final diff. Adaptive Fast-Exit is initially eligible.

## Abort evidence

A bounded caller search finds the helper re-exported through a published package entrypoint. That single fact introduces a shared public contract and the High-risk floor. Fast-Exit stops immediately; it does not keep searching or edit first to preserve a “small task” label.

Preserve the observed export path, reclassify High, load the relevant investigation and verification guidance, trace consumers, and plan compatibility and negative-path evidence proportionately. If later positive evidence proves the export is not published or consumed, risk may be lowered explicitly; patch size alone cannot do so.

## Completion semantics

The abort is a workflow transition, not task completion. Do not emit a Fast-Exit `VERIFIED` claim at the transition. Continue through Standard Engineering Mode and report only the evidence actually gathered and checks actually run after the final edit.

Only after the Standard workflow completes and its focused plus compatibility evidence passes may the final report be:

### Execution Summary
Policy: engineering-core
Risk: High
Status: VERIFIED
Changed: Renamed the helper while preserving the published compatibility contract.
Verified: Focused, consumer-compatibility, and final-diff checks passed after the final edit.
Limitations: None
