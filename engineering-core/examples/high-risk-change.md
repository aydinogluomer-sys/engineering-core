# Worked Example: High-Risk Change

## Request

“Fix an authorization bug where a user can access another tenant's export if they know the export ID.”

## Classification

- Task: security-sensitive implementation.
- Risk: High even if the final diff is one line.
- Specialist: security review is appropriate if available.

## Invariants

- A caller can access an export only when the trusted server-side authorization path proves tenant ownership or an explicitly permitted administrative capability.
- Client-side gating is not authorization.
- Denied requests do not leak export metadata.
- Existing authorized access remains functional.

## Investigation

Inspect:

- route/controller;
- authentication identity source;
- export lookup;
- tenant/ownership model;
- authorization helper/policy;
- relevant tests;
- sibling endpoints for precedent.

If a code graph exists, use it to locate callers and shared authorization helpers, then verify current source.

## Implementation

Fix the broken trusted-boundary check at the smallest correct layer.

Do not:

- hide the button and call it fixed;
- add a new authorization framework if an established policy exists;
- weaken a failing security test.

## Verification

At minimum:

- same-tenant authorized request succeeds;
- cross-tenant request fails;
- unauthenticated request follows intended behavior;
- administrative exception, if real, is verified;
- no metadata leak on denial;
- affected regression checks pass after final edit.

## Review

Use a fresh reviewer when available. Give the reviewer the request, relevant instructions, actual diff, surrounding authorization path, and test evidence.

## Completion

“High-risk fix implemented” and “verified” remain separate until current negative-path evidence exists.
