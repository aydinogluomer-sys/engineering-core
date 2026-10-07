# Contributing

Use a focused branch and keep changes within the declared scope. Do not weaken evaluator-owned oracles, delete negative-path coverage, fabricate model provenance, or convert `BLOCKED`/`NOT_RUN` into `PASS`.

Before a pull request, run:

```bash
python engineering-core/scripts/validate_skill.py engineering-core
python engineering-core/scripts/test_validate_skill.py
python -m unittest discover -s evals -p "test_*.py"
python scripts/test_validate_repository.py
python scripts/validate_repository.py .
python -m compileall -q engineering-core scripts evals
```

The pull request must identify linked requirements, affected scope, evidence commands, negative paths, limitations, and any deferred or blocked capability. Changes to scorers, protected oracles, report schemas, installers, or release gates require fresh independent review.
