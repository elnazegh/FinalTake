# Automatic Staging Deployment (FC4G6-370)

Workflow file: `.github/workflows/staging.yml` (name: **Deploy Staging**).

- Triggers when **FinalTake CI** completes successfully for a push to `main`. Failed CI runs and pull request runs never deploy. It can also be started manually with `workflow_dispatch`.
- Checks out the exact commit that passed CI and publishes `frontend/` to GitHub Pages under the `staging` environment. The deployment URL appears on the workflow run and in the repository's Environments list.
- Only the static frontend is deployed. The Flask backend and MySQL are not hosted, so search, sign-up and login do not work on the staging site.

## One-time setup (repository admin)

Settings > Pages > Build and deployment > Source: **GitHub Actions**. Until that is enabled the deploy job fails; CI itself is unaffected because staging is a separate workflow.

## Status

This workflow has not run yet. It starts working after it is merged to `main` and Pages is enabled. The `workflow_run` trigger only fires from the copy of the workflow on the default branch, so it cannot be exercised from a pull request.

## Not yet implemented

- Hosting for the backend and database in staging.
