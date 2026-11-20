# FC4G6-1087 — Manual Exploratory QA Results

**Project:** FinalTake — Sprint 5
**Test Date:** November 19, 2026
**Environment:** Local Chrome frontend (127.0.0.1:5500), Flask backend (127.0.0.1:5000), MySQL 8.0
**Reference:** FC4G6-1086 Manual Exploratory QA Checklist

## Overview

Executed browser-based exploratory tests covering authentication, search, filtering, sorting, media details, reviews, input validation, and API error handling. Results were verified through direct interaction with the running application and captured screenshots.

## Test Execution Results

| Scenario | Test Performed | Result |
|---|---|---|
| EX-01 | Registration and authenticated login | PASS |
| EX-01 | Session persistence after page refresh | PASS |
| EX-01 | Logout and unauthenticated state after navigation/refresh | PASS |
| EX-01 | Invalid login credentials rejected | PASS |
| EX-01 | Duplicate registration rejected | PASS |
| EX-02 | Search for "Dark" across media types | PASS |
| EX-02 | Movies-only filtering | PASS |
| EX-02 | Release Year: Newest First sorting | PASS |
| EX-02 | Search result navigation to media details | PASS |
| EX-03 | Valid media details displayed for The Dark Knight | PASS |
| EX-03 | Invalid media ID displays "Media not found." | PASS |
| EX-04 | Create and display a 4.5-star test review | PASS |
| EX-04 | Edit and display updated review | PASS |
| EX-04 | Delete test review and confirm removal | PASS |
| EX-05 | Missing rating prevents review submission | PASS |
| EX-05 | Unauthenticated review submission rejected | PASS |
| EX-06 | Backend outage displays user-friendly search error | PASS |
| EX-06 | Search results recover after backend restart | PASS |

## Verified Observations

- Returning from media details through "Back to Search" resets the previous query, media-type filter, and sorting selection.
- Review submission is accessible through the separate `review-form-demo.html?id=1` page; the media-details page displays reviews and owner editing/deletion controls.
- The Dark Knight displays image and description placeholders where content is unavailable.
- A nonexistent media ID displays an appropriate error message while the Reviews section remains visible.

These observations are recorded without classifying them as confirmed defects.

## Conclusion

The executed exploratory scenarios produced the expected functional results for the tested workflows. Authentication, search, filtering, sorting, media-details navigation, review CRUD, form validation, and search error recovery were verified locally. This report describes executed coverage only and does not claim exhaustive application testing.
