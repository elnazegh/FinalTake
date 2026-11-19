# FC4G6-1084 — Sprint 5 Release Readiness Checklist

**Project:** FinalTake — CPSC 491 Group 6
**Review date:** November 18, 2026
**Scope:** CI/CD configuration, staging availability, health checks, environment setup, and deployment limitations.

## 1. Verified Release Checks

- [x] CI workflow configured for pull requests and pushes to `main`.
- [x] Successful CI execution confirmed, including run #183.
- [x] CI includes backend Python tests, frontend Node.js tests, and a MySQL 8.0 test service.
- [x] Python dependency auditing and npm dependency auditing configured in CI.
- [x] Staging deployment workflow configured through GitHub Pages.
- [x] Staging deployment #18 completed successfully on November 5, 2026.
- [x] Staging homepage accessible and frontend controls visible.
- [x] Backend `/api/health` implementation reviewed.
- [x] Existing health-check error-handling test passed locally (1 test).
- [x] Local environment template and package configuration reviewed.

## 2. Release Readiness Gaps

- [ ] **Full-stack staging verification:** Searching for `Dark` displayed an error on the staging site.
- [ ] **Backend/database staging integration:** The reviewed staging workflow deploys only the static frontend.
- [ ] **Post-deployment smoke-test integration:** Implementation exists on `luis/sprint4-health-check` but was not included in the reviewed `main` workflow.
- [ ] **End-to-end staging functionality:** Authentication and other backend-dependent interactions have not been verified in staging.
- [ ] **Setup documentation:** `README.md` contains only the project title and description.

## 3. Testing and Environment Notes

- Local development settings are documented in `backend/.env.example`; environment-specific secrets must be supplied separately.
- CI executes designated Node.js test files. The `npm test` script is currently a placeholder.
- The existing backend health test verifies safe error handling, not successful live database connectivity.
- The staging smoke-test implementation checks static frontend resources, not backend availability.

## 4. Assessment

FinalTake has functioning CI and a successfully deployed static staging frontend. However, the reviewed staging deployment does not establish full application release readiness because backend-dependent functionality remains unverified and the staging search test produced an error.

**Evidence:** GitHub Actions runs #183 and #18; staging homepage and search-error screenshots; local health-check test output; reviewed CI/CD and environment configuration.