# FC4G6-1098 — Session Expiration Test Scenarios

**Project:** FinalTake — Sprint 5
**Preparation Date:** November 19, 2026
**Branch:** yk/sprint5-fc4g6-807-integration
**Inspected Commit:** 9253982

## Authentication Implementation Review

Inspected backend/app.py and confirmed:

- Authentication uses Flask sessions with session["user_id"].
- Login creates a non-permanent session.
- Logout clears the session.
- GET /api/auth/session returns HTTP 401 when unauthenticated.
- Review POST, PATCH, and DELETE routes require authentication.
- Unauthenticated review operations return HTTP 401.
- GET /api/media/<media_id> does not require authentication.
- PERMANENT_SESSION_LIFETIME is configured to eight hours, but automatic expiration has not been verified.

## Integration Test Scenarios

| ID | Scenario | Expected Result |
|---|---|---|
| S1 | Log in, log out, then search for Dark, filter Movies, sort results, and open The Dark Knight | Public search and media details remain accessible |
| S2 | Log in, prepare a review, invalidate the session, then attempt submission | Review submission is rejected and no review is created |
| S3 | Create a review, invalidate the session, then attempt editing or deletion | Unauthorized changes are rejected and review data remains unchanged |
| S4 | Attempt a protected action without authentication, then log in again | Authentication feedback appears and normal access is restored |

## Test Environment

- Local FinalTake frontend
- Flask backend
- MySQL database
- Chrome browser
- Prepared test account
- Sample media: The Dark Knight (Media ID 1)

## Testing Approach

Use the application's normal login and logout functionality to verify behavior after session invalidation.

Inspect available browser feedback and API responses. Verify that unauthorized review actions do not modify review data.

Record actual results during FC4G6-1099 and FC4G6-1100.

## Scope Limitation

Logout-based invalidation does not establish that automatic session expiration works. Actual expiration timing must be assessed separately and must not be reported as passed without verification.

No authentication configuration or application code changes are required for this test plan.
