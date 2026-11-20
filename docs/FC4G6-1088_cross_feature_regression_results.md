# FC4G6-1088 — Cross-Feature Regression Testing Results

**Project:** FinalTake — Sprint 5
**Test Date:** November 19, 2026
**Environment:** Chrome, local frontend (127.0.0.1:5500), Flask backend (127.0.0.1:5000), MySQL 8.0
**Related Task:** FC4G6-1087 Manual Exploratory QA Execution

## Overview

Executed cross-feature regression checks to verify that authentication, search, filtering, sorting, media details, and review functionality continued working together after the Flask backend was restarted.

## Regression Results

| Test | Expected Behavior | Result |
|---|---|---|
| Login after backend restart | Existing QA account can authenticate | PASS |
| Authenticated homepage | Log Out button appears | PASS |
| Search while authenticated | Searching "Dark" displays relevant results | PASS |
| Search with Movies filter | Only matching movie results appear | PASS |
| Newest First sorting | Darkest Hour (2017) precedes The Dark Knight (2008) | PASS |
| Search to media details | Clicking The Dark Knight opens the correct details page | PASS |
| Media details rendering | Title, type, genre, and release year display correctly | PASS |
| Review deletion persistence | Previously deleted test review does not reappear | PASS |
| Reviews empty state | "No reviews yet." displays after deletion | PASS |
| Navigation availability | Back to Search link remains visible | PASS |

## Verified Workflow

Login → Search → Media-Type Filtering → Sorting → Media Details → Reviews

The combined workflow was executed successfully using the locally running frontend and backend.

## Observations

- Search parameters reset when returning to the homepage through Back to Search.
- Review submission uses a separate demo form, while the media-details page supports review display and owner editing/deletion.
- The tested media item displays placeholders for unavailable image and description content.

These observations do not establish defects without comparison against project requirements.

## Conclusion

The tested cross-feature workflow passed the executed regression checks after backend recovery. The results confirm the observed integration behavior for the tested scenarios only.
