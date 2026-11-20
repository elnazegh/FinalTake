# FC4G6-1089 — Defect Documentation and Verification

**Project:** FinalTake — Sprint 5
**Review Date:** November 19, 2026
**Environment:** Local Chrome frontend, Flask backend, MySQL 8.0

## Overview

Reviewed observations from manual exploratory testing (FC4G6-1087) and cross-feature regression testing (FC4G6-1088). Checked the repository for documented requirements relevant to the observed behavior.

## Observations Reviewed

### 1. Search Settings Reset After Navigation

**Reproduction:**
1. Search for "Dark".
2. Apply the Movies filter.
3. Select Release Year: Newest First.
4. Open The Dark Knight.
5. Click Back to Search.

**Observed:** The homepage loads, but the search query, media-type filter, and sorting selection return to their defaults.

**Assessment:** Reproduced behavior. No explicit search-state preservation requirement was identified in the reviewed repository references, so this is documented as a usability observation rather than a confirmed defect.

### 2. Review Submission Uses a Separate Demo Page

**Reproduction:**
1. Open The Dark Knight's media-details page.
2. Inspect the available review controls.
3. Open review-form-demo.html?id=1 separately.

**Observed:** Media Details supports review display and owner edit/delete actions. Review creation works through the separate demo form.

**Assessment:** Reproduced behavior. The reviewed references do not explicitly require an inline review creation form, so this is documented as an integration/navigation observation rather than a confirmed defect.

## Verification Results

- Search, filtering, sorting, and media-details navigation passed the executed tests.
- Review creation, display, editing, and deletion passed.
- Invalid media IDs displayed an appropriate error.
- Unauthenticated review submission was rejected.
- Search displayed a user-friendly error during backend unavailability and recovered after restart.
- Cross-feature regression checks passed following backend recovery.

## Conclusion

No confirmed application defects were established by the completed exploratory and regression checks. Two reproducible usability observations were documented for consideration. No application fixes were performed or claimed as part of this review.
