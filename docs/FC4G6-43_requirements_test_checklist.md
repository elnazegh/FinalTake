# FinalTake — Sprint 3 Requirements-Based Test Checklist

**Jira:** [FC4G6-43 — Create Requirements-Based Test Checklist](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-43)

**Project:** FinalTake · CPSC 491-10 · Fall 2026

**Owner:** Person 5 — Search, Integration, and QA

**Baseline:** `main` at commit `5f3de7d` · local test execution 2026-10-13

**Source:** Submitted Sprint 3 Individual Test Plan (Section 5), reviewed repository files, and local test output.

> This document records requirements, existing coverage, and planned testing. A passing unit or API test does **not** establish that a frontend, authenticated, or real-database workflow has passed. Do not turn unexecuted, blocked, or historical tests into current passes.

## Status summary

| Status | Scenarios |
|---|---:|
| Pass - local | 2 |
| Partial - local | 3 |
| Not run | 10 |
| Blocked | 2 |
| Future sprint | 4 |
| **Total** | **21** |

**Status meanings:** `Pass - local` = the scenario was exercised by current local automated tests; `Partial - local` = only part of that scenario was exercised; `Not run` = no Sprint 3 execution yet; `Blocked` = dependent implementation was not ready on the reviewed branch; `Future sprint` = scheduled after Sprint 3. `Existing coverage` may refer to earlier Sprint 2 manual verification and should not be confused with this run.

## Current automated test baseline

| Source | Command / workflow | Observed result | Limitation |
|---|---|---|---|
| Local backend (2026-10-13) | `(cd backend && python3 -m unittest discover -s . -p 'test_*.py' -v)` | 20 tests; OK; 0.298s | Backend route tests; registration DB is mocked; not real MySQL proof |
| Local repository (2026-10-13) | `python3 -m unittest discover -s tests -p 'test_*.py' -v` | 54 tests; OK; 0.011s | Includes structural/frontend, model, and in-memory review API tests; not full browser integration |
| GitHub Actions PR (2026-10-08 (historical)) | `FinalTake CI • backend-tests + frontend-validation` | Both jobs reported passed (Sprint 2) | Historical baseline; current Sprint 3 GitHub run not yet inspected |
|  (FUTURE EXECUTION LOG • add rows only after actually running/verifying the test or workflow) | `` |  |  |
| Source (Date) | `Command or workflow` | Observed result | Confidence / limitation |

**Verification:** The local tests were executed on `main` at `5f3de7d`. Current GitHub Actions results and actual database-backed workflows must be verified separately. The 20 backend tests and 54 repository tests are different suites; do not treat their sum as a count of covered requirements.

## Checklist scenarios

Mark a scenario complete only when the scenario itself has been verified, not merely because an associated unit test passed. Keep coverage evidence and execution status separate.

### Search / filtering / sorting

#### ST-01 — Valid or partial title search

- [x] **Execution:** Pass - local  ·  **Jira:** [FC4G6-677](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-677)
- **Requirement:** FR5
- **Expected result:** Matching media are returned according to search requirements
- **Method:** Automated functional / regression  ·  **When:** Sprint 3
- **Existing evidence:** backend/test_search.py: partial, middle, case-insensitive matches; 20/20 local backend tests passed
- **Coverage assessment:** Automated - checked
- **Follow-up / owner:** Reuse passing assertions; rerun if search code changes [Search QA]

#### ST-02 — Genre, media-type, and combined filters

- [x] **Execution:** Pass - local  ·  **Jira:** [FC4G6-677](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-677)
- **Requirement:** FR5
- **Expected result:** Results satisfy selected genre/type criteria
- **Method:** Automated regression  ·  **When:** Sprint 3
- **Existing evidence:** backend/test_search.py: genre, media type, combined, no-match combinations
- **Coverage assessment:** Automated - checked
- **Follow-up / owner:** Reuse existing filter tests; inspect only newly changed behavior [Search QA]

#### ST-03 — Sort search results

- [ ] **Execution:** Partial - local  ·  **Jira:** [FC4G6-677](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-677)
- **Requirement:** FR5 + agreed sort choices
- **Expected result:** Results follow the selected supported sorting order
- **Method:** Automated regression  ·  **When:** Sprint 3
- **Existing evidence:** backend/test_search.py tests title_asc and year_desc; app.py also supports title_desc and year_asc
- **Coverage assessment:** Partial - checked
- **Follow-up / owner:** Confirm team-agreed sort options and whether remaining directions warrant coverage [Search QA]

#### ST-04 — Search yielding no matches

- [ ] **Execution:** Partial - local  ·  **Jira:** [FC4G6-677](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-677)
- **Requirement:** FR5
- **Expected result:** Backend returns empty results; UI displays applicable empty state
- **Method:** Automated API / previous manual UI  ·  **When:** Sprint 3
- **Existing evidence:** test_no_match and combined-filter no-match pass locally; frontend no-results state manually verified in Sprint 2
- **Coverage assessment:** Partial - checked
- **Follow-up / owner:** Reuse backend tests; selectively recheck UI after integration changes [Search QA]

#### ST-05 — Empty and whitespace-only query

- [ ] **Execution:** Partial - local  ·  **Jira:** [FC4G6-677](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-677)
- **Requirement:** FR5 / input behavior to confirm
- **Expected result:** Defined behavior is consistent and produces no unexpected failure
- **Method:** Boundary / equivalence  ·  **When:** Sprint 3
- **Existing evidence:** test_missing_query passes; test_whitespace_is_trimmed checks surrounding spaces, not whitespace-only; JS returns early for blank query
- **Coverage assessment:** Partial - checked
- **Follow-up / owner:** Confirm expected blank-query UI behavior; decide if focused assertion is justified [Search QA]

#### ST-06 — Special-character or unusually long query

- [ ] **Execution:** Not run  ·  **Jira:** [FC4G6-677](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-677)
- **Requirement:** FR5 / limits to confirm
- **Expected result:** Input follows agreed API contract; no unhandled exception
- **Method:** Boundary / negative  ·  **When:** Sprint 3
- **Existing evidence:** No matching special-character or long-query assertion identified in reviewed search tests
- **Coverage assessment:** Unconfirmed
- **Follow-up / owner:** Check specification/API contract before selecting inputs or writing tests [Search QA]

#### ST-07 — Invalid or missing filter value

- [ ] **Execution:** Not run  ·  **Jira:** [FC4G6-677](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-677)
- **Requirement:** FR5 / invalid filter behavior to confirm
- **Expected result:** Defined validation or fallback behavior, not an assumed error code
- **Method:** Negative / API  ·  **When:** Sprint 3
- **Existing evidence:** app.py uses equality filters and recognized sort branches; invalid-parameter assertions not found in reviewed tests
- **Coverage assessment:** Unconfirmed
- **Follow-up / owner:** Confirm desired invalid filter/sort behavior; add a test only for a justified gap [Search QA]

### Frontend / backend integration

#### IT-01 — Frontend request reaches relevant backend route

- [ ] **Execution:** Not run  ·  **Jira:** [FC4G6-675](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-675)
- **Requirement:** FR5 / API contract
- **Expected result:** Correct route and parameters; expected results render in UI
- **Method:** Integration  ·  **When:** Sprint 3
- **Existing evidence:** frontend/js/app.js constructs /api/search query; FC4G6-275 manually verified basic integration in Sprint 2
- **Coverage assessment:** S2 manual evidence
- **Follow-up / owner:** Check a representative request on Sprint 3 build and record URL/response [Search/API QA]

#### IT-02 — API error followed by successful request

- [ ] **Execution:** Not run  ·  **Jira:** [FC4G6-675](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-675)
- **Requirement:** FR5 / error behavior to confirm
- **Expected result:** UI handles failure and later returns to a consistent usable state
- **Method:** Negative / state transition  ·  **When:** Sprint 3-4
- **Existing evidence:** app.js has try/catch and error message; no matching frontend recovery assertion in tests/test_frontend.py
- **Coverage assessment:** Implementation only
- **Follow-up / owner:** Execute targeted failure-recovery check when suitable; Sprint 4 follow-up FC4G6-701 [Search/API QA]

#### IT-03 — Search -> results -> details -> back

- [ ] **Execution:** Not run  ·  **Jira:** [FC4G6-677](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-677)
- **Requirement:** FR5 + FR6
- **Expected result:** Selected media details open; search usable after return
- **Method:** Scenario / end-to-end  ·  **When:** Sprint 3; 5-6
- **Existing evidence:** app.js links to media-details.html with encoded id; FC4G6-275 reported working navigation in Sprint 2
- **Coverage assessment:** S2 manual evidence
- **Follow-up / owner:** Repeat once after Sprint 3 integration changes; record build/browser [Search navigation QA]

### Backend / database integration

#### DB-01 — Applicable backend/database read

- [ ] **Execution:** Not run  ·  **Jira:** [FC4G6-676](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-676)
- **Requirement:** FR1 / DB-backed paths
- **Expected result:** Expected persistent record returned or documented error; test DB only
- **Method:** Integration  ·  **When:** Sprint 3
- **Existing evidence:** backend/database.py connects to MySQL; database_test.py manually queries users; not included in CI discovery
- **Coverage assessment:** Implementation only
- **Follow-up / owner:** Confirm safe test DB and database-backed route with DB owner; do not use sample search data [Integration QA / DB teammate]

#### DB-02 — Applicable persistent write/read-back

- [ ] **Execution:** Not run  ·  **Jira:** [FC4G6-676](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-676)
- **Requirement:** FR1 / persistence
- **Expected result:** Permitted write is reflected in a subsequent read from test DB
- **Method:** Integration / persistence  ·  **When:** Sprint 3
- **Existing evidence:** /api/auth/register writes users; test_registration.py mocks MySQL and does not prove persistence
- **Coverage assessment:** Partial - checked
- **Follow-up / owner:** Coordinate a safe fixture/test account and non-production DB; no production writes [Integration QA / DB teammate]

### Authentication with protected features

#### AU-01 — Signed-out user accesses protected action

- [ ] **Execution:** Blocked  ·  **Jira:** [FC4G6-678](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-678)
- **Requirement:** FR2 / protected features
- **Expected result:** Unauthorized operation denied according to agreed access rules
- **Method:** Integration / negative  ·  **When:** Sprint 3 if ready
- **Existing evidence:** login/logout return 501 in current main; session-protected flow unavailable there
- **Coverage assessment:** Blocked - dependency
- **Follow-up / owner:** Revisit after auth branch merges; auth developer owns login tests [Integration QA / Auth teammate]

#### AU-02 — Signed-in user uses protected feature

- [ ] **Execution:** Blocked  ·  **Jira:** [FC4G6-678](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-678)
- **Requirement:** FR2 + feature access
- **Expected result:** Authenticated state recognized across required components
- **Method:** Integration / state transition  ·  **When:** Sprint 3 if ready
- **Existing evidence:** Current main lacks working login/logout; cannot verify authenticated integration
- **Coverage assessment:** Blocked - dependency
- **Follow-up / owner:** Coordinate readiness and select one supported protected action [Integration QA / Auth teammate]

### Social/Reviews

#### SO-01 — Media, rating, review, or favorite interaction

- [ ] **Execution:** Not run  ·  **Jira:** [FC4G6-679](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-679)
- **Requirement:** FR7-FR14 (verify specifics)
- **Expected result:** Correct API response and consistent applicable UI/account state
- **Method:** Cross-feature integration  ·  **When:** Sprint 3 if ready
- **Existing evidence:** review API CRUD tests and rating/favorites object-flow tests pass; reviews use in-memory storage
- **Coverage assessment:** Partial - checked
- **Follow-up / owner:** Choose one supported cross-component flow with feature owner; do not repeat unit tests [Integration QA / Social teammate]

#### SO-02 — Tag/social interaction across views

- [ ] **Execution:** Not run  ·  **Jira:** [FC4G6-679](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-679)
- **Requirement:** FR10-FR17 (verify specifics)
- **Expected result:** Consistent tag/social state where feature is integrated
- **Method:** Scenario-based integration  ·  **When:** Sprint 3 if ready
- **Existing evidence:** No tag/social integrated flow confirmed from current main files inspected; teammate branch exists
- **Coverage assessment:** Unconfirmed
- **Follow-up / owner:** Confirm which tagged/social actions are implemented and merged; mark Blocked if unavailable [Integration QA / Social teammate]

### CI/CD verification

#### CI-01 — Relevant CI checks on Sprint 3 PR or commit

- [ ] **Execution:** Not run  ·  **Jira:** [FC4G6-681](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-681)
- **Requirement:** Sprint 2 CI/CD plan
- **Expected result:** Relevant jobs run; results and build ID recorded
- **Method:** Automated regression / CI  ·  **When:** Throughout Sprint 3
- **Existing evidence:** ci.yml runs on PR/push main, backend+repo tests, frontend file checks; local 20/20 and 54/54; Sprint 2 Draft PR #27 passed
- **Coverage assessment:** CI configured
- **Follow-up / owner:** Verify current GitHub Actions run for target commit or next Sprint 3 PR [Integration QA / CI owner]

### Manual QA

#### MT-01 — Repeated searches, filters, and sort changes

- [ ] **Execution:** Future sprint  ·  **Jira:** [FC4G6-702](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-702)
- **Requirement:** FR5 / user workflows
- **Expected result:** UI remains usable; results reflect current inputs
- **Method:** Exploratory / scenario  ·  **When:** Sprint 5
- **Existing evidence:** Scheduled for Sprint 5 manual QA; no Sprint 5 execution claimed
- **Coverage assessment:** Planned future
- **Follow-up / owner:** Prepare concise manual sequence and environment details in Sprint 5 [Search QA]

#### MT-02 — Unexpected but reasonable navigation sequence

- [ ] **Execution:** Future sprint  ·  **Jira:** [FC4G6-702](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-702)
- **Requirement:** FR5 + FR6
- **Expected result:** No broken user state; issues reproducible
- **Method:** Exploratory / scenario  ·  **When:** Sprint 5
- **Existing evidence:** Scheduled for Sprint 5 manual QA; no Sprint 5 execution claimed
- **Coverage assessment:** Planned future
- **Follow-up / owner:** Record steps, actual behavior and screenshots when executed [Search/navigation QA]

### Final regression and smoke testing

#### FT-01 — Run applicable final regression suites

- [ ] **Execution:** Future sprint  ·  **Jira:** [FC4G6-703](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-703)
- **Requirement:** Sprint 6 final regression
- **Expected result:** Tests pass or failures recorded on identified final build
- **Method:** Regression  ·  **When:** Sprint 6
- **Existing evidence:** Planned final testing; not executable as final release check yet
- **Coverage assessment:** Planned future
- **Follow-up / owner:** Use identified release candidate and GitHub Actions run ID [Search/integration QA]

#### FT-02 — Final critical user workflow smoke test

- [ ] **Execution:** Future sprint  ·  **Jira:** [FC4G6-703](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-703)
- **Requirement:** FR5 + FR6 / agreed integrations
- **Expected result:** No unresolved blocking search/integration defects, or explicit escalation
- **Method:** Smoke / focused E2E  ·  **When:** Sprint 6
- **Existing evidence:** Planned final smoke testing; no execution claimed
- **Coverage assessment:** Planned future
- **Follow-up / owner:** Test complete chosen workflow and report unresolved blockers [Search/integration QA]

## Evidence to add as tests are performed

For each executed scenario, record: test ID; date; branch/commit or build number; setup/browser/test data; steps or command; expected vs. actual behavior; Pass/Fail/Blocked/Not run; and supporting terminal output, screenshot, CI URL, or defect issue. Do not record passwords or other credentials.

## Jira issue references

| Sprint | Ticket | Planned scope |
|---|---|---|
| Sprint 3 | [FC4G6-43](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-43) | Requirements-based testing checklist |
| Sprint 3 | [FC4G6-675](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-675) | Frontend/backend integration |
| Sprint 3 | [FC4G6-676](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-676) | Backend/database integration |
| Sprint 3 | [FC4G6-677](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-677) | Search → results → media details |
| Sprint 3 | [FC4G6-678](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-678) | Authentication and protected features |
| Sprint 3 | [FC4G6-679](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-679) | Ratings/reviews/favorites/tags/social integration |
| Sprint 3 | [FC4G6-680](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-680) | Log and verify integration bugs |
| Sprint 3 | [FC4G6-681](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-681) | Verify CI/CD and automated test integration |
| Sprint 4 | [FC4G6-701](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-701) | API error handling and recovery |
| Sprint 5 | [FC4G6-702](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-702) | Manual exploratory QA |
| Sprint 6 | [FC4G6-703](https://finaltake-cpsc491.atlassian.net/browse/FC4G6-703) | Final regression and smoke testing |

## Coordination / scope notes

- Review the official FinalTake specification when exact accepted inputs, expected errors, and FR wording are uncertain; FR references above follow the earlier project-specification summary.
- Treat the login/logout placeholders on reviewed `main` as a feature-readiness dependency, not a passing or failing authenticated-integration test.
- For database checks, use a safe test environment and confirmed database-backed routes. `backend/database_test.py` is a manual read script and is not included in `test_*.py` CI discovery.
- Existing registration tests mock the MySQL connection, while existing review data is held in memory. Neither proves real database persistence.
- Do not duplicate teammates’ feature-level tests or rewrite passing Sprint 2 tests solely to produce more commits. New automated tests should target confirmed, meaningful gaps.
- Update this file when features merge, contracts change, defects are reproduced, or new tests/CI results are available.

## FC4G6-43 follow-through

- [x] Review current repository, core search/integration implementation, tests, and CI configuration.
- [x] Run local backend and repository suites and record the results.
- [ ] Confirm any unresolved requirement wording and review this checklist with relevant feature owners.
- [ ] Commit this checklist to the project repository and link it in FC4G6-43.
- [ ] Record outstanding coverage gaps and dependencies under the related testing Jira issues.
