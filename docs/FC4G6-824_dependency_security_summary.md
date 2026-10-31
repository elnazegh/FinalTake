# FC4G6-824 — Dependency Vulnerability Scanning

## Objective
Identify known vulnerabilities in FinalTake's frontend and backend dependencies, apply targeted updates, and verify the results.

## Initial Findings
- Frontend: `npm audit` reported 0 vulnerabilities.
- Backend: `pip-audit` reported 18 findings across 3 packages.

## Dependency Updates

| Package | Previous Version | Updated Version |
|---------|------------------|-----------------|
| PyJWT | 2.13.0 | 2.15.0 |
| python-dotenv | 1.2.1 | 1.2.2 |
| Werkzeug | 3.1.8 | 3.1.9 |

Only these three dependency pins were changed in `backend/requirements.txt`.

## Verification
- Installed the updated dependencies in an isolated Python environment.
- `pip check` reported no broken requirements.
- Backend tests: 35 passed, 1 MySQL-dependent test skipped.
- Repository Python tests: 107 passed.
- Re-ran `pip-audit` against the updated requirements file.
- Final result: No known vulnerabilities found.

## Evidence
- `FC4G6-824_npm_audit.json`
- `FC4G6-824_python_audit.json`
- `FC4G6-824_python_audit_after.json`
- `FC4G6-824_requirements_audit_after.json`

## Remaining Verification
- Confirm regression tests in GitHub Actions using CI's Python environment.
- Obtain teammate PR review and approval before merging.

## Limitations
A clean dependency audit does not guarantee that the application is free of security vulnerabilities. The isolated regression test run did not execute the MySQL-dependent integration test.
