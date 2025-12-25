# Testing & CI

Purpose
- Describe how tests are organized, how to run them locally, and what to watch for in CI.

Where tests live
- `tests/` — unit tests for individual modules.
- `tests/integration/` — integration tests that may hit external services or larger flows.

Running tests locally
- If using `pytest` (likely), run:

```bash
python -m pytest -q
```

- To run a single test file:

```bash
python -m pytest tests/test_pipeline.py -q
```

Test types
- Unit tests: small, fast, mock external I/O. Examples: `tests/test_adjuster.py`, `tests/test_resampling.py`.
- Integration tests: may require network or credentials; kept under `tests/integration`. These are typically skipped in CI unless credentials are provided.

Fixtures and mocks
- Shared fixtures live in `tests/conftest.py` and `tests/integration/conftest.py`. They configure test data, temporary directories, and mock clients.
- Use mocks for network calls to avoid flakiness and rate limits.

CI notes
- CI should run unit tests and linters. Integration tests can be gated behind a flag or run in a separate job with credentials/secrets.
- Cache dependencies (pip cache, virtualenv) to speed up runs.

Common test commands

```bash
# run all tests
python -m pytest
# run a single test
python -m pytest tests/test_resampling.py::test_time_resample
# run with coverage
python -m pytest --cov=src --cov-report=term-missing
```

Where to read next
- `pytest.ini` or `pyproject.toml` for test config
- `tests/` for concrete examples of how modules are exercised

Would you like me to run the test suite locally or open specific files for deeper explanation?
