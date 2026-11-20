# FC4G6-1099 — Public Search After Session Invalidation

**Project:** FinalTake — Sprint 5
**Test Date:** November 19, 2026
**Branch:** yk/sprint5-fc4g6-807-integration
**Tested Commit:** 00b8244

## Test Environment

- Local frontend: http://127.0.0.1:5500/frontend/
- Flask backend: http://127.0.0.1:5000
- Browser: Google Chrome
- Authentication: Flask session-based
- Invalidation method: Normal application logout

## Verification Results

| Test | Result |
|---|---|
| Login using a test account | PASS |
| Logout returns user to login page | PASS |
| Public search for "Dark" after logout | PASS — Four results |
| Movies filter after logout | PASS — Two results |
| Release Year: Newest First | PASS — Correct order |
| Open The Dark Knight Media Details | PASS |
| Display reviews empty state | PASS |

## Observed Behavior

After logging out, the application returned to the login page and displayed Log In and Sign Up controls.

Public search remained accessible. Searching for "Dark" returned The Dark Knight, Dark, Darkest Hour, and Dark Souls.

Filtering by Movies returned The Dark Knight and Darkest Hour. Sorting by Release Year: Newest First displayed Darkest Hour (2017) before The Dark Knight (2008).

Selecting The Dark Knight opened the correct Media Details page with its title, media type, genre, release year, and "No reviews yet" message.

## Conclusion

All executed public media discovery checks passed after normal logout.

The test verified logout-based session invalidation behavior, not automatic session expiration. No application code changes were required.
