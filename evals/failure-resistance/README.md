# Failure-resistance evaluation

This suite separates deterministic scorer/fixture validation from live-model reliability. Run:

```bash
python -m unittest discover -s evals/failure-resistance -p "test_*.py"
```

The source-discovery, coordination, specialist-routing, and prompt-injection cells are deterministic. The stack runner provisions exact TypeScript and Playwright packages in an isolated temporary cache, uses a discovered local Chrome/Edge executable, and runs PostgreSQL 17.6 in a disposable non-published Docker container:

```bash
python evals/failure-resistance/run_stack_integrations.py
```

The evaluator-owned oracles require a known-bad baseline to fail, the corrected fixture to pass, and protected fixture/oracle hashes to remain unchanged. The PostgreSQL oracle exercises real RLS roles, session context, grants, reads, writes, owner behavior, and a BYPASSRLS service path. The browser oracle exercises rendered state, click blocking, keyboard/focus, authorization messaging, and console errors. Missing safe tooling remains `BLOCKED`; no mock, static parser, screenshot, or production service can produce PASS.
