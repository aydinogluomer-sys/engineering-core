# Worked Example: Small Fix

## Request

“Fix the typo in the API error message.”

## Classification

- Task: small correction.
- Risk: Low.
- Scope: one localized string and its nearest test/precedent.

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

Implemented:
- Corrected the typo in the API error message.

Verified:
- Targeted test/check passed after the edit.
- Final diff contains only the intended string change.

Limitations:
- None beyond the scoped check, unless broader verification was required by repository policy.
