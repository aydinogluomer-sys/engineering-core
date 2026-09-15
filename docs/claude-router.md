# Optional CLAUDE.md Routing

`engineering-core` is model-invocable, but skill activation is model-driven and should not be treated as deterministic.

If you want the skill to be consistently considered for substantive engineering work in a repository, you may add the following to that repository's `CLAUDE.md`:

> For substantive software-engineering implementation, debugging, refactoring, migration, review, or release work, apply the `engineering-core` skill unless a more specific applicable instruction supersedes its workflow mechanics.

This is optional guidance.

It does not:

- guarantee activation;
- provide deterministic enforcement;
- replace Claude Code permissions, sandboxing, managed policy, or hooks;
- authorize consequential actions.

`engineering-core` does not modify `CLAUDE.md` automatically.
