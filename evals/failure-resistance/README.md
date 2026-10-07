# Failure-resistance evaluation

This suite separates deterministic scorer/fixture validation from live-model reliability. Run:

```bash
python -m unittest discover -s evals/failure-resistance -p "test_*.py"
```

The source-discovery, coordination, specialist-routing, and prompt-injection cells are deterministic. Stack fixtures are present for TypeScript, PostgreSQL/RLS, and browser interaction, but their integration cells are `BLOCKED` unless `tsc`, `psql`, and a supported local browser executable are discovered. A blocked capability is never promoted to a pass, and no production service is contacted.
