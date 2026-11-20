# FC4G6-1085 — Deployment and Recovery Procedures

**Project:** FinalTake — CPSC 491 Group 6
**Review date:** November 19, 2026

## 1. Deployment Procedure

FinalTake uses GitHub Actions for continuous integration and GitHub Pages for static frontend staging deployment.

1. Create a feature branch for the changes.
2. Submit a pull request targeting `main`.
3. Obtain teammate review and approval.
4. Confirm that FinalTake CI passes.
5. Merge the approved pull request into `main`.
6. After a successful CI run triggered by the push to `main`, the Deploy Staging workflow automatically publishes the frontend.
7. Verify the staging deployment through GitHub Actions.

Staging URL:
https://elnazegh.github.io/FinalTake/

## 2. CI Failure Recovery

If FinalTake CI fails:

1. Open GitHub Actions and identify the failed workflow run.
2. Inspect the failed job and its logs.
3. Identify the failing test, dependency audit, or validation step.
4. Correct the issue on the appropriate feature branch.
5. Push the correction and allow CI to execute again.
6. Obtain the required review and approval before merging.

A failed CI run prevents the automatic staging deployment from proceeding.

## 3. Staging Deployment Failure Recovery

If Deploy Staging fails:

1. Open the failed Deploy Staging workflow run.
2. Inspect the failed deployment step and logs.
3. Check GitHub Pages configuration and the repository staging environment.
4. Correct the identified configuration or deployment issue.
5. Use a reviewed pull request for code or workflow changes.
6. Verify the next successful staging deployment.

The workflow also supports manual execution through `workflow_dispatch`. Manual execution does not require a preceding successful CI run, so it should not replace the normal reviewed deployment process.

## 4. Frontend Rollback Procedure

If a merged change causes a staging regression:

1. Identify the commit responsible for the regression.
2. Prepare a Git revert on a separate branch.
3. Submit the revert through a pull request.
4. Obtain teammate review and approval.
5. Confirm CI passes before merging.
6. Verify the resulting staging deployment.

This is a documented recovery procedure; a rollback execution has not been verified during this review.

## 5. Database Recovery Limitations

- Database configuration is provided through environment variables documented in `backend/.env.example`.
- Database initialization is represented by `backend/schema.sql`.
- Application transaction failures use `connection.rollback()` where implemented.
- No repository-managed database backup or restoration scripts were identified in the searched repository paths.
- Transaction rollback does not replace a full database backup and restoration procedure.

Database backup and restoration therefore remain operational gaps that require a separately established procedure.

## 6. Staging Limitations

- GitHub Pages currently deploys only the static frontend.
- Flask and MySQL are not hosted by the reviewed staging workflow.
- The staging homepage was accessible during the November 18, 2026 verification.
- Searching for "Dark" displayed an error during that verification.
- A post-deployment smoke-test implementation exists on `origin/luis/sprint4-health-check`. It checks static frontend resources but does not verify backend or database connectivity. It is not included in the reviewed `main` workflow.

## 7. Verification Evidence

- GitHub Actions: FinalTake CI and Deploy Staging.
- Successful staging deployment #18, November 5, 2026.
- Staging homepage and search-error screenshots, November 18, 2026.
- Local backend health-check test: 1 test passed.
- Reviewed CI/CD configuration, database configuration, and environment template.
