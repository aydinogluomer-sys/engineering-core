# Repository governance

## Prepared branch-protection profile

This is a prepared configuration, not evidence that GitHub settings have been applied.

- Require pull requests and the `static-validation` matrix before merge.
- Dismiss stale approvals after substantive changes when independent reviewers are used.
- Block force pushes and branch deletion on the default branch.
- Keep administrator bypass explicit and auditable; do not silently bypass failing evidence gates.
- For a single-maintainer repository, do not require an unavailable second human reviewer. Preserve user-controlled merge while requiring CI and recording independent machine review evidence where appropriate.

Application requires separate authorization. After application, read settings back through the GitHub API and save the observed response; a prepared policy must never be labeled applied.

## Action pin updates

Resolve official tags with `git ls-remote` against the action's official repository, inspect the resolved commit, replace the immutable SHA while retaining the major-version comment, and run repository validation. Never guess a SHA.
