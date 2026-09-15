# Safety Profiles

Read this reference for security-sensitive work and changes involving databases, authentication/authorization, billing, secrets, destructive actions, production state, or external side effects.

## 1. Security escalation

Trigger deeper review when a change crosses a trust boundary, including:

- authentication;
- authorization;
- permissions/admin;
- session/token handling;
- secrets/PII;
- payments/billing/credits;
- webhooks;
- uploads/downloads;
- user-controlled URLs;
- serialization;
- SQL construction;
- database functions;
- RLS;
- infrastructure privileges;
- CI secrets;
- cryptography;
- cross-tenant data.

Evaluate relevant boundaries:

`input -> identity -> authorization -> data -> side effect -> failure`

Use threat-relevant reasoning rather than a generic checklist.

Consider:

- insecure defaults;
- fail-open behavior;
- sharp edges;
- variant search;
- differential review;
- post-patch validation.

Route to a trusted specialist security skill when depth or uncertainty warrants it.

## 2. Database profile

For database/migration work, consider:

- migration ordering;
- locks and long transactions;
- compatibility window;
- backfill strategy;
- idempotency;
- uniqueness;
- concurrent writers;
- rollback versus forward-only constraints;
- existing production rows;
- triggers;
- transaction boundaries;
- RLS/tenant behavior;
- grants/roles;
- restore/recovery evidence.

### PostgreSQL / Supabase

Also inspect, when relevant:

- anonymous/authenticated/service roles;
- direct table access;
- privileged RPC exposure;
- `SECURITY DEFINER`;
- `search_path`;
- function ownership;
- role grants;
- migration ordering;
- generated types as output, not authority.

Do not blindly require reversibility. Some production migrations are correctly forward-only.

## 3. Authentication / authorization profile

Verify enforcement at the trusted boundary.

Consider:

- server-side authorization;
- session/token lifecycle;
- privilege escalation;
- default-deny behavior;
- tenant isolation;
- revocation;
- enumeration;
- CSRF/replay when relevant;
- admin/service bypass paths;
- client-side gating versus actual authorization.

Client-side hiding is presentation, not an authorization boundary.

## 4. Billing / payments / side-effect profile

For financial state, credits, AI-provider charging, webhooks, queues, and other side effects, consider:

- stable idempotency identity;
- money units/rounding;
- duplicate suppression;
- at-least-once delivery reality;
- exactly-once effect when required;
- retries;
- replay;
- duplicate/out-of-order events;
- provider call count;
- process death;
- locks/leases;
- partial completion;
- state-machine transition legality;
- reconciliation;
- refunds/reversals;
- test/live separation;
- auditability.

Verify externally observable invariants, not only internal flags.

## 5. Git and user-work safety

Before destructive or broad Git/filesystem actions:

- inspect worktree status;
- identify user-owned changes;
- verify exact paths/targets;
- prefer recoverable operations.

Do not discard, overwrite, stash, reset, clean, rewrite history, delete branches, or force-push user work without exact scope and authority.

Unknown existing changes are user-owned until evidence says otherwise.

## 6. Secret safety

Treat as sensitive:

- `.env` values;
- private keys;
- cloud credentials;
- service-account files;
- tokens;
- signing keys;
- production database URLs;
- CI secrets.

Prefer safe examples/schemas/environment variable names.

Never print, commit, transmit, place in prompts, fixtures, diffs, or observability events, or copy secrets into reports.

If a secret is accidentally exposed, redact it from further output and treat rotation as a separate consequential action requiring appropriate authority.

## 7. Destructive / production actions

The skill is behavioral policy, not enforcement.

Permissions, sandboxing, managed policy, PreToolUse hooks, Safety Net, DCG, or similar controls may provide deterministic blocking.

Do not install or modify those controls unless explicitly requested.

For Critical actions, verify exact current authorization. If the user's current instruction explicitly authorizes the exact action and target, complete required gates and proceed without redundant confirmation. Otherwise stop immediately before the action and request exact authority.

## 8. External side effects

External messages, deployments, destructive API calls, production writes, credential rotations, and irreversible provider actions are distinct from local preparation.

Authorization to draft, review, validate, or stage does not imply authorization to send, deploy, mutate, rotate, or delete.
