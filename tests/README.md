Run all tests with coverage:

```
pytest -q --maxfail=1 --disable-warnings --cov=backend/app --cov-report=term-missing --cov-report=html:tests/htmlcov
```

Reports are stored under `tests/htmlcov` (HTML coverage) and displayed in console.
Tests use in-memory SQLite and disable rate limiting by default.

Test groups:
- API basics: health, admin auth, basic contract checks
- Database: schema and CRUD
- Script flow: collection endpoint contract


