# Worked Example: Removal Task

## Request

“Remove the legacy analytics provider from this subsystem.”

## Classification

- Task: removal.
- Risk: Moderate or High depending on runtime/data/release effects.

## Removal contract

“Removed” means no unintended live dependency remains.

## Investigation

Find:

- imports/exports;
- runtime initialization;
- API calls;
- routes/handlers;
- configuration;
- environment variables;
- feature flags;
- dependency manifests;
- tests/mocks;
- build/CI references;
- docs;
- generated artifacts;
- database/IaC references when applicable.

Use Cartographer-style removal audit if available and fresh; otherwise use native search and repository tooling.

## Implementation

Delete only after dependent surfaces are understood.

Avoid replacing the provider with a new architecture unless requested.

## Verification

- build/type checks no longer reference the provider;
- focused runtime tests pass;
- package/dependency state is clean if removal requires it;
- search/completeness audit finds no unintended live references;
- configuration/env cleanup is complete where authorized.

## Completion

Deleting the primary adapter file is not sufficient evidence.

Report any intentionally retained historical docs/migrations separately from live runtime references.
