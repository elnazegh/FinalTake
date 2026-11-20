# FC4G6-1103 — Keyboard Access to Search and Filtering Controls

**Project:** FinalTake — Sprint 5
**Test Date:** November 19, 2026
**Branch:** yk/sprint5-fc4g6-807-integration
**Tested Revision:** d5ac082

## Test Environment

- Local FinalTake frontend and Flask backend
- Google Chrome on macOS
- macOS Keyboard Navigation enabled
- Keyboard-only interaction

## Verified Results

| Test | Result |
|---|---|
| Navigate to search field using Tab | PASS |
| Submit search for Dark using keyboard | PASS |
| Operate media-type dropdown | PASS |
| Select Movies filter | PASS |
| Operate sorting dropdown | PASS |
| Select Release Year: Newest First | PASS |
| Apply filtering and sorting using keyboard | PASS |

## Observed Behavior

The search field was reachable using the keyboard, and searching for Dark returned the expected four media results.

The media-type and sorting dropdowns were operable without a mouse. Applying the Movies filter and Release Year: Newest First returned Darkest Hour (2017) followed by The Dark Knight (2008).

All executed keyboard interaction checks passed.

## Scope

Testing covered keyboard operation of the search field, filter, sorting dropdown, and Search button.

Focus-indicator visibility and full navigation order will be assessed separately under FC4G6-1104.

No application code changes were performed.
