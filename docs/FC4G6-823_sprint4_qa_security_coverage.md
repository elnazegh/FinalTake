# FC4G6-823 — Sprint 4 QA and Security Test Coverage Review

**Project:** FinalTake

**Course:** CPSC 491-10 — Fall 2026

**Sprint:** Sprint 4 (October 29–November 5, 2026)

**Role:** Search / Integration / QA

**Assessment date:** October 29, 2026

**Working branch:** `yk/sprint4-fc4g6-823-qa-coverage`

**Related SOC 2-aligned criterion:** CC7.1 (vulnerability detection and monitoring)

## 1. Purpose and scope

Review existing QA and security-related test coverage, establish a reproducible local baseline, identify gaps, and record follow-up work for Sprint 4. This is a **coverage review**, not a completed SOC 2 assessment. Security-related functional tests are supporting evidence; CC7.1 will also require vulnerability and configuration review under other Jira subtasks.

## 2. Test inventory

The repository inventory found **19 test files**:

| Test group | Files | Notes |
| --- | ---: | --- |
| Backend Python (`backend/test_*.py`) | 4 | Authentication, registration, search, database integration |
| Repository Python (`tests/test_*.py`) | 9 | Comments, favorites, frontend files, ratings, reviews, drafts, and social integration |
| Node.js (`tests/*.test.mjs`) | 3 | Authentication UI errors, media details, search integration |
| Playwright (`tests/*.spec.js`) | 3 | Signup, logout, media details |
| **Total** | **19** | Inventory only; not every file was executed individually |

The repository also contains `.github/workflows/ci.yml`, `.github/workflows/staging.yml`, `package.json`, and `playwright.config.js`.

## 3. Verified local test baseline

The following commands and results were supplied from the local Sprint 4 working branch:

| Test suite | Command | Pass | Fail | Status |
| --- | --- | ---: | ---: | --- |
| Backend authentication | `python3 -m unittest discover -s backend -p 'test_authentication.py' -v` | 14 | 0 | Pass |
| Backend search | `python3 -m unittest discover -s backend -p 'test_search.py' -v` | 14 | 0 | Pass |
| Repository Python | `python3 -m unittest discover -s tests -p 'test_*.py' -v` | 107 | 0 | Pass |
| Frontend Node.js | `node --test tests/*.test.mjs` | 8 | 0 | Pass |
| **Distinct tests in these suites** | | **143** | **0** | **Pass** |

**Counting note:** The 19 review API tests were run separately (19/19 passing) but are included in the 107 repository Python tests. The single search integration test was also run separately (1/1 passing) but is included in the eight Node.js tests. Neither is counted twice.

**Not yet verified:** Backend registration and database integration suites as part of the full backend suite, Playwright browser tests, and a fresh GitHub Actions run for this branch. Local pass results should not be represented as CI results.

## 4. Security-related coverage observed

| Area | Existing evidence | Assessment |
| --- | --- | --- |
| Authentication and session lifecycle | 14 backend authentication tests passed: valid/invalid login, missing/malformed input, unauthorized session access, logout/session invalidation, and tested database-error behavior | Existing coverage confirmed |
| Review API authorization | Tests for unauthenticated create/edit/delete, non-owner edit/delete, forged `user_id`, and logout behavior are included in the 107 repository tests | Existing coverage confirmed; primarily another group member's access-control scope |
| Search behavior | 14 backend search tests passed: missing/whitespace queries, title matching, genre/type filters, combined filters, sorting, result shape | Functional baseline confirmed |
| Frontend API error handling | Eight Node tests passed, including authentication 401/503/network errors, media details 404/500/network errors, and search recovery after a mocked 500 | Mocked frontend behavior confirmed; not a live-backend security assessment |
| Dependency vulnerability detection | No dependency vulnerability scan step found in the provided `ci.yml` | Gap to assess under FC4G6-824 |
| Security configuration review | No review results supplied yet | Pending FC4G6-825 |

## 5. Identified coverage gaps and CI observations

These are **review findings and candidates for verification**, not confirmed exploitable vulnerabilities.

1. **Search input security edges:** `backend/test_search.py` does not explicitly test unusually long/malformed search values, unsupported filter/sort values, or sensitive data disclosure in errors. Follow up under **FC4G6-805** and **FC4G6-701**.
2. **Live backend error disclosure:** The observed frontend search recovery test simulates an HTTP 500, but does not verify that an actual Flask error response hides tracebacks, paths, or secrets. Follow up under **FC4G6-701 / FC4G6-826**.
3. **Dependency vulnerabilities:** The inspected CI workflow has no `npm audit`, `pip-audit`, or equivalent dependency vulnerability scanning step. Assess actual dependencies and findings under **FC4G6-824**.
4. **Security configuration:** Debug settings, secret handling, and exposure controls have not yet been assessed for Sprint 4. Follow up under **FC4G6-825**; never paste secret values into evidence.
5. **Repository Python CI command:** The provided `ci.yml` uses `python -m unittest discover -s tests -p "test_*.py"-v`. The missing space can cause `-v` to join the test pattern, potentially discovering zero tests. Confirm and correct in a reviewed PR.
6. **Media-details CI logging command:** The provided `ci.yml` uses `| tee"$RUNNER_TEMP/media-details-tests.log"`. Without a separating space, the shell can treat the combined token as a command name. Confirm and correct in a reviewed PR.
7. **Browser tests in CI:** Three Playwright spec files were inventoried but no Playwright execution step was present in the provided `ci.yml`. Evaluate separately; running browser tests requires appropriate setup.
8. **`npm test` script:** `package.json` contains a placeholder failing `test` script. This does not prevent the observed direct `node --test` commands from running; consider whether a standard script would help future development.
9. **Evidence retention:** CI workflow defines Python and frontend test-log artifacts with seven-day retention. Record the run URLs and preserve any required evidence before artifact expiration.

## 6. Recommended follow-up by Jira task

| Jira | Follow-up |
| --- | --- |
| FC4G6-823 | Save this inventory, baseline, and gap assessment; verify/fix CI command issues through a reviewed PR if within scope |
| FC4G6-824 | Run dependency vulnerability scans and record severity, affected dependencies, and remediation status |
| FC4G6-825 | Review security-relevant application configurations and document sanitized findings |
| FC4G6-826 | Validate security regression coverage without duplicating teammate-owned authorization tests |
| FC4G6-701 | Test real API error behavior, sensitive information exposure, and frontend recovery |
| FC4G6-805 | Test malformed/unexpected input and filter edge cases |
| FC4G6-827 | Record repeatable search API performance smoke-test results |
| FC4G6-828 | Collect GitHub Actions logs, scan reports, PRs, and Jira evidence for the CC7.1 assessment |

## 7. FC4G6-823 acceptance checklist

- [x] Inventory existing frontend and backend test files.
- [x] Inspect the CI and testing configuration supplied for review.
- [x] Identify security-related test scenarios present in the inspected files and test names.
- [x] Execute and record the selected local authentication, review, search, repository, and Node.js baselines.
- [x] Document gaps and recommended Sprint 4 follow-up actions.
- [ ] Save this checklist in the repository and submit it for PR review/approval.

## 8. Evidence and limitations

**Evidence currently available:** Local terminal output for authentication (14 passed), review API (19 passed separately), search backend (14 passed), search frontend (1 passed separately), full repository Python tests (107 passed), and all Node.js tests (8 passed); test source and CI workflow contents reviewed in the conversation.

**Limitations:** No fresh CI run, browser-test execution, full backend-suite execution, security scanner output, configuration review result, or production security assessment has yet been established here. A passing regression suite does not prove absence of vulnerabilities or full SOC 2 compliance.

**Next action:** Commit this review document on `yk/sprint4-fc4g6-823-qa-coverage`, request teammate review through a PR, and continue to FC4G6-824 after the baseline documentation is handled.
