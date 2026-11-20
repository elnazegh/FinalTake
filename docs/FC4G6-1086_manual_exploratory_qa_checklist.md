# FC4G6-1086 — Manual Exploratory QA Scenarios

**Project:** FinalTake — CPSC 491 Group 6
**Review date:** November 19, 2026
**Scope:** Manual exploratory test scenarios for implemented application workflows.

## 1. Testing Scope

The checklist covers authentication, media discovery, media details, reviews, ratings, navigation, invalid inputs, and error handling.

Scenarios focus on integrated application behavior rather than duplicating existing automated regression tests.

## 2. Exploratory QA Scenarios

### EX-01 — Authentication and Session Behavior

- Open the login page and authenticate using valid test credentials.
- Verify that the session is established.
- Log out and verify that the session is terminated.
- Attempt to access protected review actions without authentication.

**Expected result:** Valid authentication succeeds, logout terminates the session, and unauthorized actions are restricted.

### EX-02 — Search, Filtering, Sorting, and Navigation

- Search for an existing media title.
- Apply an available media-type filter.
- Change the available sorting option.
- Open a result from the filtered list.
- Navigate back to search.

**Expected result:** Search results reflect the selected query, filters, and sorting. The selected result opens the corresponding media details.

### EX-03 — Media Details Loading

- Open a media item from search results.
- Verify that its title and available details correspond to the selected result.
- Attempt to open the details page without a media ID.
- Test an invalid or nonexistent media ID.

**Expected result:** Valid media details load correctly. Invalid or missing identifiers do not display unrelated media information or cause an unhandled application error.

### EX-04 — Review Display and Ownership

- Open a media item with existing reviews.
- Verify that displayed reviews belong to the selected media.
- Log in as the review owner and inspect available edit/delete controls.
- Log in using another test account and inspect the same review.
- Use a disposable test review to avoid modifying shared project data.
- Test the edit and delete confirmation interactions.

**Expected result:** Reviews are associated with the correct media. Review management controls respect ownership and authorization.

### EX-05 — Review Submission and Rating

- Open the standalone review form using a valid media ID.
- Select a rating using the standalone form's dropdown.
- Submit a review with nonempty text.
- Verify that the submission succeeds.
- Open the corresponding media details page and check the submitted review.
- Test missing ratings, empty review text, and unauthenticated submission.

**Expected result:** Valid submissions are accepted and associated with the correct media. Invalid inputs and unauthorized submissions are rejected with appropriate feedback.

### EX-06 — Navigation and Error Handling

- Navigate between search and media details.
- Test behavior when the backend is unavailable.
- Observe application feedback when API requests fail.
- Verify that failed requests do not display misleading or unrelated data.

**Expected result:** Navigation remains usable and API failures produce appropriate user-facing feedback without exposing internal server details.

## 3. Existing Feature Integration Limitations

The following implementation boundaries were identified during repository inspection:

- Comments currently use temporary in-memory JavaScript data and are not connected to backend persistence.
- The visual half-star rating selector is demonstrated separately and has not been established as part of the review submission workflow.
- Review submission is available through a standalone demo page rather than the main Media Details page.
- Favorites frontend/backend integration has not been established.
- Tag-following has a registered backend API, but frontend integration has not been established.

These limitations are considered when determining which scenarios are applicable to the integrated application.

## 4. Existing Automated Test Coverage

The repository contains automated test files for authentication, search, media details, reviews, ratings, comments, favorites, and tag-related functionality.

The presence of these tests does not establish that every scenario is integrated or executed by CI. Manual exploratory testing will emphasize integrated user workflows, navigation, and behavior that cannot be established solely through isolated automated tests.

## 5. Evidence Requirements

For executed exploratory scenarios, retain:

- Test scenario ID and execution date.
- Tested application environment and branch/commit.
- Steps performed.
- Expected and actual behavior.
- Pass, fail, blocked, or partial outcome.
- Supporting screenshots or reproducible defect details.