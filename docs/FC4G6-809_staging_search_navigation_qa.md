# FC4G6-809 — Staging Search and Navigation QA

**Project:** FinalTake — Sprint 5
**Test Date:** November 19, 2026
**Environment:** Chrome, GitHub Pages staging
**Staging URL:** https://elnazegh.github.io/FinalTake/

## Overview

Performed manual staging verification of homepage rendering, media-category navigation, search functionality, and error handling.

## Test Results

| Test | Result | Observation |
|---|---|---|
| Staging homepage | PASS | Homepage renders successfully |
| Movies navigation | PASS | Media-type filter updates to Movies |
| TV Shows navigation | PASS | Corresponding media-type filter selected |
| Books navigation | PASS | Corresponding media-type filter selected |
| Games navigation | PASS | Corresponding media-type filter selected |
| Search for "Dark" | FAIL | Search API request returns HTTP 404 |
| Search error handling | PASS | Friendly error message displayed |
| Filtered search results | BLOCKED | Search API unavailable |
| Sorted search results | BLOCKED | Search API unavailable |

## Confirmed Staging Integration Issue

**Issue:** Search requests fail in the deployed staging environment.

**Reproduction:**
1. Open https://elnazegh.github.io/FinalTake/
2. Enter "Dark" in the search field.
3. Click Search.
4. Inspect the browser console.

**Expected:** Relevant media results are displayed.

**Actual:** The page displays "Unable to load search results. Please try again."

**Observed Request:**
GET https://elnazegh.github.io/api/search?query=Dark

**Observed Status:** HTTP 404 Not Found

**Assessment:** The staging frontend sends the search request to GitHub Pages, where the Flask API endpoint is unavailable. The local integrated application successfully returned search results during FC4G6-1087 testing.

**Disposition:** Confirmed staging integration issue requiring coordination with the deployment/backend owner. No deployment fix was implemented during this QA task.

## Conclusion

Staging homepage rendering and media-category navigation passed. Search functionality failed because the deployed API endpoint returned HTTP 404. Search-dependent filtering and sorting could not be fully verified in staging.
