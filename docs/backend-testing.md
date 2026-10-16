# Backend Testing Guide (Sprint 3)

Stack: Python 3.12, Flask, MySQL (`mysql-connector-python`), `unittest`.

## Test layout

| File | Type | Needs MySQL |
|---|---|---|
| `backend/test_backend_unit.py` | Unit tests (DB mocked): `database.py`, health, media lookup, search edge cases, review validation, registration DB handling | No |
| `backend/test_db_integrity.py` | CRUD, constraints, NULL/length limits, failed-operation consistency, schema checks on `users` | Yes |
| `backend/test_db_integration.py` | Flask routes against a real test DB (registration, health) plus media catalog round trips | Mostly (media class does not) |
| `backend/db_test_support.py` | Fixture: creates a throwaway database from `schema.sql`, cleans up | n/a |

Existing teammate tests (`backend/test_search.py`, `backend/test_registration.py`, `tests/*`) are unchanged.

## Run the tests

From the repository root, after `pip install -r backend/requirements.txt`:

```powershell
# Backend tests (unit tests run; DB tests skip without a test MySQL server)
cd backend
python -m unittest discover -s . -p "test_*.py" -v

# Repository-level tests
cd ..
python -m unittest discover -s tests -p "test_*.py" -v
```

## Run the database tests

Point the tests at a MySQL server where creating and dropping databases is safe. These variables are separate from the app's `DB_*` variables on purpose, so the shared dev database is never touched.

```powershell
$env:TEST_DB_HOST = "127.0.0.1"
$env:TEST_DB_USER = "<test user with CREATE/DROP privileges>"
$env:TEST_DB_PASSWORD = "<password>"   # never commit this
$env:TEST_DB_PORT = "3306"             # optional
cd backend
python -m unittest test_db_integrity test_db_integration -v
```

- Each test class creates `finaltake_test_<random>` from `backend/schema.sql` and drops it when done; rows are deleted after every test.
- The fixture refuses to drop any database without the `finaltake_test_` prefix or equal to `DB_NAME`.
- Without `TEST_DB_*`, or if the server is unreachable, DB tests are skipped. Set `REQUIRE_DB_TESTS=1` to fail instead.

## Coverage

`coverage` is a local dev tool and is not in `requirements.txt`.

```powershell
pip install coverage
cd backend
python -m coverage run --include="app.py,database.py,review.py" -m unittest discover -s . -p "test_*.py"
python -m coverage report -m
```

## Scope and limitations

- Only the `users` table exists in `schema.sql`. There are no foreign keys, so FK and invalid-reference tests do not apply yet.
- The media catalog and reviews are in-memory in `backend/app.py`, not MySQL. There is no media create/update/delete code, so media tests cover retrieval by ID and search only.
- `database.py`'s `__main__` block is not covered, by design.
- Observation (not changed): registration accepts a whitespace-only username or password because it only checks for falsy values.

## CI notes for Sprint 4

Current CI (`.github/workflows/ci.yml`) already runs the backend and `tests/` suites with `unittest` and starts a throwaway `mysql:8.0` service. It sets `DB_*` variables for a `finaltake_ci_test` database, but the tests in this guide read `TEST_DB_*`, so they skip in CI and CI stays green. To run them in CI:

1. Export `TEST_DB_HOST=127.0.0.1`, `TEST_DB_USER=root` and `TEST_DB_PASSWORD` (the service's root password; the fixture needs a user that can create and drop databases) and `REQUIRE_DB_TESTS=1` for the backend test step, so a missing DB fails the build instead of skipping.
2. Optionally add `coverage` and a minimum-coverage gate.

CI dependencies: everything in `backend/requirements.txt` (`mysql-connector-python`, `Flask`, `python-dotenv`, `Werkzeug`), plus `coverage` if a gate is added.
