# Automatic Staging Deployment (FC4G6-370)

Workflow file: `.github/workflows/staging.yml` (name: **Deploy Staging**).

- Triggers when **FinalTake CI** completes successfully for a push to `main`. Failed CI runs and pull request runs never deploy. It can also be started manually with `workflow_dispatch`.
- Checks out the exact commit that passed CI and publishes `frontend/` to GitHub Pages under the `staging` environment. The deployment URL appears on the workflow run and in the repository's Environments list.
- Only the static frontend is deployed. The Flask backend and MySQL are not hosted, so search, sign-up and login do not work on the staging site.

## One-time setup (repository admin)

Settings > Pages > Build and deployment > Source: **GitHub Actions**. Until that is enabled the deploy job fails; CI itself is unaffected because staging is a separate workflow.

## Status

This workflow has run on `main` and deploys the frontend to the `staging` environment, which is published at `https://elnazegh.github.io/FinalTake/` (Pages source: GitHub Actions). The `workflow_run` trigger only fires from the copy of the workflow on the default branch, so changes to this workflow cannot be exercised from a pull request; they take effect after they are merged to `main`.

## Post-Deployment Smoke Test – FC4G6-374

Script: `scripts/check_staging.py` (Python standard library only). It runs as the **Verify staging deployment** step in `.github/workflows/staging.yml`, immediately after the GitHub Pages deployment step, using the deployment URL (`page_url`) from that step.

- The smoke test runs after GitHub Pages deployment.
- It checks that the homepage (`index.html`), the stylesheet (`css/style.css`) and the main JavaScript file (`js/app.js`) are accessible and return HTTP 200 with a non-empty body.
- It validates the expected FinalTake homepage content: the homepage must contain `<title>FinalTake</title>` and `js/app.js` must contain `API_BASE_URL`.
- Failed checks are retried up to six times, waiting 10 seconds between attempts, to allow for GitHub Pages propagation delay. Retried failures include HTTP errors, unexpected content, timeouts, connection resets, SSL errors and truncated or malformed HTTP responses.
- Persistent failures cause the GitHub Actions job to fail (exit code 1), which marks the staging deployment run as failed.
- The Flask backend and database are not verified by this test because they are not hosted in the existing staging environment. The test covers the deployed static frontend only; the backend `/api/health` endpoint is not called.
- A workflow failure does not automatically roll back the deployed site. The already-published version stays live until it is replaced by a later deployment.

To run the check manually against a deployment (the URL must be HTTPS):

```
python scripts/check_staging.py --url https://<owner>.github.io/<repository>/
```

Automated tests for the script are in `tests/test_smoke_check.py` and run with the repository tests in CI.

## Not yet implemented

- Hosting for the backend and database in staging.
