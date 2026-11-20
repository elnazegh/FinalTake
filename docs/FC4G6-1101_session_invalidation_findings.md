# FC4G6-1101 — Session Invalidation Integration Findings

**Project:** FinalTake — Sprint 5
**Verification Date:** November 19, 2026
**Branch:** yk/sprint5-fc4g6-807-integration
**Tested Revision:** 00b8244 through c72a44b

## Overview

Consolidated the authentication integration review and manual verification results for public media discovery and protected review interactions.

## Verification Results

| Test Area | Result | Finding |
|---|---|---|
| Public search after logout | PASS | Four results returned for Dark |
| Media filtering | PASS | Movies filter returned two results |
| Media sorting | PASS | Newest First order was correct |
| Public Media Details | PASS | The Dark Knight loaded while logged out |
| Review submission after logout | PASS | Submission rejected with login feedback |
| Review editing after logout | PASS | Edit rejected with authorization feedback |
| Review deletion after logout | PASS | Delete rejected with authorization feedback |
| Review integrity | PASS | Existing review remained unchanged after refresh |
| Authentication recovery | PASS | Login restored Edit/Delete controls |
| Automatic session expiration | NOT VERIFIED | Natural session timeout was not observed |
| API status codes | NOT CAPTURED | Verification was performed through the browser |

## Authentication Implementation

The inspected Flask backend uses session-based authentication with session["user_id"].

Login creates a non-permanent session, logout clears the session, and protected review creation, editing, and deletion routes check for an authenticated user.

PERMANENT_SESSION_LIFETIME is configured to eight hours. However, the application uses non-permanent sessions, and automatic expiration behavior was not established by these tests.

## Observed Integration Behavior

After normal logout, public search, filtering, sorting, and media-details navigation continued to work correctly.

Protected review submission was rejected with "Please log in before submitting a review."

Review editing and deletion after logout were rejected with authorization feedback. The saved review remained unchanged after refreshing the media-details page.

Logging in again restored the authenticated user's Edit and Delete controls.

## Testing Limitations

- Logout-based session invalidation is not equivalent to automatic session expiration.
- Automatic expiration timing was not verified.
- HTTP response status codes for the manual protected-action attempts were not separately captured.
- A local Flask restart during testing reset previously stored in-memory review data. The deletion scenario was repeated without restarting either server and passed.

## Supporting Evidence

- FC4G6-1098 — Session invalidation test scenarios
- FC4G6-1099 — Public search after logout results
- FC4G6-1100 — Protected media session results

## Conclusion

All executed browser-level integration scenarios passed following logout-based session invalidation. Public media discovery remained available, protected review actions were rejected, and authentication recovery worked correctly.

Automatic session expiration remains unverified. No application code changes were performed.
