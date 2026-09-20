# Worked Example: Small Fix

## Request

“Fix the typo in the API error message.”

## Classification and Fast-Exit eligibility

- Task: small correction.
- Risk: Low.
- Scope: one localized string and its nearest test/precedent.
- Evidence: reversible, unambiguous, no shared contract or consequential domain, focused proof available.

## Execution

1. Read applicable repository instructions.
2. Inspect the target string and nearest related test/usage.
3. Hold the change contract:
   - behavior: correct the typo only;
   - surface: target file, test only if wording is asserted;
   - proof: targeted test or static check plus diff.
4. Make the minimum edit.
5. Run the narrowest meaningful check.
6. Inspect final diff/status.
7. Report what changed and what was verified.

## Deliberately not done

- no architecture map;
- no threat model;
- no subagents;
- no implementation plan document;
- no full test suite unless repository policy requires it;
- no cleanup of adjacent wording.

## Example completion report

### Execution Summary
Policy: engineering-core
Risk: Low
Status: VERIFIED
Changed: Corrected the typo in the API error message.
Verified: Targeted check passed after the edit; final diff contains only the intended string change.
Limitations: None.
