# Optional persistent Reviews storage (MySQL)

This change deliberately leaves the original in-memory Reviews flow active by default.
The demo can continue using its existing behavior until the team elects to switch.

## Setup for an existing local MySQL database

1. Back up the local FinalTake database before applying schema changes.
2. Open MySQL Workbench or another MySQL SQL editor connected to `finaltake_db`.
3. Run `backend/migrations/001_reviews.sql` against that database. It creates only
   the new `reviews` table and does not delete existing tables.
4. Add this setting to your **local** `backend/.env` file:

   `REVIEW_STORAGE_BACKEND=mysql`

5. Restart the Flask backend. The API paths and frontend stay the same.
6. Sign in as a **real MySQL user**, post a test review, refresh, and restart Flask.
   The review should still appear; edit and deletion should work for its owner.
7. Repeat with a second logged-in account: the second account must not be able to
   update or delete the original account's review.

## Safety and compatibility notes

- To return to the old demo behavior, set `REVIEW_STORAGE_BACKEND=memory` and
  restart Flask. This switches the storage source; it does not delete SQL reviews.
- In-memory reviews from an earlier Flask run are **not automatically migrated**.
  Set up a fresh sample review after enabling SQL storage.
- If SQL mode is enabled without the new table or a working database connection,
  Review endpoints return HTTP 503. They intentionally do **not** silently fall
  back to temporary storage.
- `media_id` is stored as text until Luis's unmerged Media CRUD PRs have been
  integrated. The current hardcoded media IDs continue to work.
- `user_id` references the existing `users` table, so the Review owner must be
  a registered database user.
- The new SQL tests use a lightweight SQL adapter to verify persistence and
  authorization without modifying any team database. A live **MySQL** regression
  run is still required before claiming production or demo readiness.
- Do not commit local `.env` values, passwords, database dumps, or test accounts.
