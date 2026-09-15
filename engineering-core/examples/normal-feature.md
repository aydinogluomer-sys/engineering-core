# Worked Example: Normal Feature

## Request

“Add an optional display name to team profiles and show it in the member list.”

## Classification

- Task: feature/change.
- Risk: Moderate.
- Expected surface: model/type, write path, read path, UI, tests.

## Bounded investigation

Inspect:

- applicable repository instructions;
- team profile type/model;
- existing profile update pattern;
- member-list consumer;
- nearest validation and tests;
- migration/schema only if persistence requires it.

Stop once these questions are answered:

- Where is the source of truth?
- Is the field already available but unused?
- What validation/length/nullability convention exists?
- Which callers/consumers are affected?

## Plan

1. Extend the established profile contract with an optional display name.
2. Update the existing write path using current validation patterns.
3. Render the value with the repository's fallback behavior.
4. Add/adjust focused tests for present and absent values.
5. Run relevant type/static/integration checks.
6. Review final diff for scope drift.

## Verification

Cover:

- display name present;
- display name absent;
- validation boundary;
- existing profile behavior unchanged;
- relevant integration/type checks.

### UI/browser slice

Because the value is rendered, use existing component or browser tooling when available to verify present, absent/fallback, and one relevant narrow/interactive state. Do not install browser tooling for this task. If UI behavior is a required acceptance criterion and no equivalent evidence is available, report it as `NOT_VERIFIED` rather than treating model tests as proof of rendering.

## Scope discipline

Do not:

- redesign the profile model;
- add a new form framework;
- rename unrelated fields;
- change member-list styling beyond what the feature requires.

## Completion

Claim only the checks actually run after the final edit.
