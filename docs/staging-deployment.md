# Automatic Staging Deployment (FC4G6-370)

Workflow: `.github/workflows/staging.yml` (`Deploy Staging`).

## Deployment Configuration

- Runs automatically after `FinalTake CI` succeeds on a push to `main`.
- Can also be triggered manually using `workflow_dispatch`. Manual runs are not gated by a preceding successful CI run.
- Checks out the commit associated with the successful CI run for automatic deployments.
- Publishes the `frontend/` directory to GitHub Pages.
- Uses the GitHub Actions `staging` environment.

Staging URL: https://elnazegh.github.io/FinalTake/

## Repository Setup

GitHub Pages must use **GitHub Actions** as its deployment source under Settings > Pages > Build and deployment.

## Verified Deployment Status

As of November 18, 2026:

- GitHub Actions shows 18 staging workflow runs.
- The latest run, #18, completed successfully on November 5, 2026.
- Run #18 deployed commit `762a17c`.
- The staging homepage was confirmed accessible on November 18, 2026.
- The navigation menu and search, filtering, and sorting controls were visible.

## Verified Limitations

- The staging workflow deploys only the static frontend.
- The Flask backend and MySQL database are not hosted by this workflow.
- A search for "Dark" on November 18, 2026 displayed: "Unable to load search results. Please try again."
- End-to-end search and authentication functionality cannot be confirmed through the current static deployment alone.

## Deployment Evidence

- Successful staging workflow:
  https://github.com/elnazegh/FinalTake/actions/runs/42150222238
- Successful deployment #18: November 5, 2026.
- Staging homepage and search-error screenshots: November 18, 2026.
