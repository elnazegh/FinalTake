# CI/CD Workflow

Workflow file: `.github/workflows/ci.yml` (name: **FinalTake CI**). Jira: FC4G6-286, 288, 289, 290, 291. Staging deployment (FC4G6-370) is in `.github/workflows/staging.yml`.

## Triggers

- Push to `main`.
- Pull request targeting `main`.

## Jobs

| Job | Purpose | Jira |
|---|---|---|
| `backend-tests` | Python 3.12 on `ubuntu-latest` with a throwaway MySQL 8.0 service. Installs `backend/requirements.txt`, runs backend and `tests/` unit tests, packages the app, validates the package, uploads it as an artifact. | 286, 288, 289 |
| `frontend-validation` | Checks required frontend files exist, syntax-checks `frontend/js/app.js`, runs the Node tests in `tests/`. | 286, 289 |
| `ci-status` | Always runs after the two jobs above and fails unless both succeeded. | 290 |

### `backend-tests` steps

1. Check out and set up Python 3.12 (pip cache keyed on `backend/requirements.txt`).
2. Generate build version `build-<run number>-<short sha>`.
3. Install dependencies (`pip install -r requirements.txt`). A bad or missing dependency fails the job here.
4. Run `python -m unittest discover -s . -p "test_*.py" -v` in `backend/`.
5. Run `python -m unittest discover -s tests -p "test_*.py" -v` from the repo root.
6. Package `backend/`, `frontend/` and `README.md` into `<build version>.zip`.
7. Validate the build: `python -m compileall -q backend` (syntax check) and confirm the zip contains `backend/app.py`, `backend/requirements.txt`, `frontend/index.html` and `README.md`.
8. Upload the zip as a workflow artifact.

The MySQL service uses CI-only credentials defined in the workflow (`finaltake_ci_test` database). Database integration tests only run when `RUN_MYSQL_INTEGRATION_TESTS=1`, which is set only in CI, and they refuse to run unless `DB_NAME=finaltake_ci_test`.

## Run the same checks locally

```powershell
pip install -r backend/requirements.txt
cd backend; python -m unittest discover -s . -p "test_*.py" -v
cd ..; python -m unittest discover -s tests -p "test_*.py" -v
node --test tests/search_integration.test.mjs tests/media_details.test.mjs
```

Database integration tests are skipped locally unless a disposable MySQL database named `finaltake_ci_test` is configured through the `DB_*` variables and `RUN_MYSQL_INTEGRATION_TESTS=1` is set. Never point them at a shared database.

## Pass/fail behavior (FC4G6-290)

- Any failing step fails its job: a failed install, a failing or erroring test, a syntax error found by `compileall`, a missing file in the package, or a missing frontend file.
- `ci-status` turns the individual job results into one check named **CI status**. It fails if either job failed, was cancelled, or was skipped, and passes only when both succeeded.
- The pull request shows a green check only when all three jobs pass.

### How to verify pass and fail behavior

Use a throwaway branch and PR; do not merge it.

1. **Pass:** open a PR with no failing tests. Expect `backend-tests`, `frontend-validation` and `CI status` all green.
2. **Fail:** on the throwaway branch add a test such as `self.assertEqual(1, 2)` in `backend/`, push, and expect `backend-tests` and `CI status` red.
3. **Recover:** revert the commit, push, and expect all three green again.

Record the run URLs and results in the PR description. As of this document, the pass and fail runs have not been recorded.

### Recommended repository setting

Under Settings > Branches > branch protection for `main`, require the **CI status** check so a red run blocks merging. This needs repository admin access.

## Build artifacts

Each run uploads `build-<run number>-<short sha>.zip` (backend, frontend, README) to the run's Artifacts section.

## Automatic staging deployment (FC4G6-370)

Workflow file: `.github/workflows/staging.yml` (name: **Deploy Staging**).

- Triggers when **FinalTake CI** completes successfully for a push to `main`. Failed CI runs and pull request runs never deploy. It can also be started manually with `workflow_dispatch`.
- Checks out the exact commit that passed CI and publishes `frontend/` to GitHub Pages under the `staging` environment. The deployment URL appears on the workflow run and in the repository's Environments list.
- Only the static frontend is deployed. The Flask backend and MySQL are not hosted, so search, sign-up and login do not work on the staging site.

One-time setup (repository admin): Settings > Pages > Build and deployment > Source: **GitHub Actions**. Until that is enabled the deploy job fails; CI itself is unaffected because staging is a separate workflow.

Status: this workflow has not run yet. It starts working after it is merged to `main` and Pages is enabled.

## Not yet implemented

- Hosting for the backend and database in staging.
- Test coverage reporting and a coverage threshold.
