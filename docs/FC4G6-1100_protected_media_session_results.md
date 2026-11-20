# FC4G6-1100 — Protected Media Interactions After Session Invalidation

**Project:** FinalTake — Sprint 5
**Test Date:** November 19, 2026
**Branch:** yk/sprint5-fc4g6-807-integration
**Environment:** Local frontend, Flask backend, Chrome
**Invalidation Method:** Normal application logout

## Testing Summary

Manually verified that protected review interactions are rejected after logout and that authentication can be restored without losing the existing review.

Test media: The Dark Knight (Media ID 1).

## Verified Results

| Test | Result |
|---|---|
| Review form accessible while authenticated | PASS |
| Review submission rejected after logout | PASS |
| Login-required submission feedback displayed | PASS |
| Unauthorized review not created | PASS |
| Review editing rejected after logout | PASS |
| Review deletion rejected after logout | PASS |
| Saved review preserved after refresh | PASS |
| Reauthentication restores Edit/Delete controls | PASS |

## Observed Behavior

### Review Submission

Prepared a 4.5-star review while authenticated, then logged out in a separate browser tab before submitting.

The application displayed "Please log in before submitting a review." The attempted review did not appear in Media Details.

### Review Editing

An edit attempted after logout was rejected with the message "You are not authorized to edit this review."

### Review Deletion

Created a review containing "FC4G6-1100 deletion verification." and invalidated the session through logout.

The attempted deletion was rejected with the message "You are not authorized to delete this review."

After refreshing the page, the review remained visible with its original 4.5-star rating and text.

### Authentication Recovery

Logged in again using the test account. The saved review remained visible, and Edit/Delete controls became available again.

## Testing Scope

These results verify observable browser behavior after logout-based session invalidation.

API response status codes were not separately captured. Automatic session expiration was not tested.

A local Flask server restart occurred during testing, resetting the earlier in-memory review. The deletion test was repeated successfully without restarting the servers.

## Conclusion

All executed manual protection and authentication-recovery checks passed. Protected review actions were rejected after logout, and the existing review remained unchanged.

No application code changes were performed.
