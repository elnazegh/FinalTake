# Media Catalog Management - Create Media

Create, Read, Update, and Delete are delivered as separate pull requests.

## API

`POST /api/media` creates a media record in MySQL.

- Requires a logged-in session (401 otherwise).
- Requires the user to be listed in the `media_managers` table (403 otherwise).
  Permission is checked against the database on every request, so removing a
  user from `media_managers` takes effect immediately.
- JSON body: `title` (required), `type` (required: `movie`, `tv`, `book`, `game`),
  and optional `releaseYear` (1000 to current year + 10), `genre`,
  `imageUrl` (http or https only) and `description`.
- Returns 201 with `id`, `message`, and the created `media` object.

`GET /api/media/permissions` returns `{"canManageMedia": true|false}` so the
frontend can show or hide media management controls. It only reports the current
user's own permission and never grants anything. The backend enforces
permission on every create request regardless of what the frontend shows.

## Applying the schema

`backend/schema.sql` uses `CREATE TABLE IF NOT EXISTS` for every table, so it
can be run against a fresh database or an existing installation. It adds the
`media` and `media_managers` tables and never alters or drops `users`,
`password_reset_tokens` or any existing rows. For example:

```
mysql -u <admin_user> -p <database_name> < backend/schema.sql
```

`-p` with no value makes the client prompt for the password, so it is not
stored in shell history or in any file.

Existing media tables are not altered by `CREATE TABLE IF NOT EXISTS`.
Before deploying Delete Media to an existing installation, run the explicit
soft-delete migration described below.

## Granting media management access

There is intentionally no API endpoint for granting access. A database
administrator grants and revokes access directly in MySQL, using their own
credentials:

1. Connect with the MySQL client and enter the password at the prompt:
   `mysql -u <admin_user> -p <database_name>`
2. Find the user's ID: `SELECT user_id, username FROM users WHERE username = '<username>';`
3. Grant access: `INSERT INTO media_managers (user_id) VALUES (<user_id>);`
4. Verify: `SELECT user_id FROM media_managers;`
5. Revoke access: `DELETE FROM media_managers WHERE user_id = <user_id>;`

Do not commit credentials or user IDs to the repository. The application's
own database user only needs SELECT on `media_managers`, so it does not need
permission to grant access.

## GUI

Open `frontend/pages/add-media.html` while logged in as a media manager. The
Add Media link on the home page appears only for media managers. Anonymous
users and non-managers see a notice instead of the form.

## Read Media (PR 2)

`GET /api/media`, `GET /api/media/<id>`, and `GET /api/search` read from the
MySQL `media` table. Search and details retain their existing response shapes,
so newly created media appears through the existing search and details
interface after the demo catalog has been seeded.

- `GET /api/media` returns `{"media": [...]}`.
- `GET /api/media/<id>` returns the media object directly, or 404 when absent.
- `GET /api/search` returns `{"results": [...]}` and supports `query`, `genre`,
  `media_type`, and the existing title/year sort options.

Before switching an existing database to the Read endpoints, run the schema
and seed steps below. The seed is explicit and is never run as part of a
normal application request. It is intended for initial database setup, not
for routinely restoring demo data after users edit the catalog.

```powershell
cd backend
python seed_media.py
```

The script inserts the five legacy records with IDs 1–5 only when those IDs
are free and no matching title/type record exists under another ID. Re-running
it against the same seeded catalog inserts nothing. If an ID or title/type
conflict is found, it reports the conflict and makes no changes. Back up the
database and resolve the conflict manually before retrying; do not overwrite
or delete a record to force the seed through.

The MySQL `media` table is the source of truth after seeding. Reviews,
ratings and favorites remain in memory and are not made persistent by Read.
They retain media IDs as strings; keeping the legacy IDs stable is important
for their current in-process references and existing tests.

`image_url` is validated as http or https on write. Pages that render it
should still treat it as untrusted.

## Update Media (PR 3)

`PATCH /api/media/<id>` requires a logged-in user listed in `media_managers`.
The server checks permission on every request, independently of the GUI.
Send a nonempty JSON object containing any of `title`, `type`, `genre`,
`releaseYear`, `imageUrl`, and `description`. Create's validation rules apply.
Unknown fields are rejected. Omitted fields are left unchanged; optional
fields may be cleared with `null`. The ID cannot be changed.

For example:

```json
{"genre": "Adventure", "description": "A sample adventure movie used to demonstrate database updates."}
```

On success the response is HTTP 200 with the complete updated media object in
the same camelCase format as `GET /api/media/<id>`. A no-op update also returns
200. Invalid or empty input returns 400, an unauthenticated request returns
401, a non-manager receives 403, and a missing record returns 404. Database
failures return a generic 500.

### GUI and demonstration

1. Log in as a media manager and create a **new** movie named
   `Sprint 5 Demo Movie`, with type Movie, release year 2026, and genre
   Science Fiction. Do not edit the seeded IDs 1–5 for this demonstration.
2. Find the movie in search and open its details. Select **Edit Media**.
   The form is prefilled; change the genre to `Adventure` and the description
   to `A sample adventure movie used to demonstrate database updates.`
3. Save, confirm the success message, return to details, and refresh. The
   updated genre and description remain visible.

The Edit control is shown only when the permissions endpoint confirms manager
access. The update endpoint independently enforces that access.

### Limitations and validation

The seed checks exact legacy values. If an administrator edits a seeded row,
a later seed run reports a collision and makes no changes. Investigate and
back up the database before resolving it manually; do not overwrite edits or
disable collision checks. Reviews, ratings, and favorites retain their
existing in-memory behavior. Concurrent edits to the same field use the last
committed value; there is no version-conflict warning.

Local validation on the Update branch: 101 backend tests and 187 repository
tests passed with isolated MySQL 8.0.40, including Create, Read, and the new
update persistence test. Eleven Node regression tests and four Playwright
browser tests passed; those browser tests mock API responses. A separate
local browser check also created and edited a new movie against the isolated
MySQL database and confirmed its values after refreshing.

## Delete Media (PR 4)

`DELETE /api/media/<id>` requires an authenticated user listed in
`media_managers`, checked on every request. It returns 200 with
`{"message": "Media deleted successfully."}`, 401 without a session, 403
without permission, 404 for a missing or already-deleted record, and a generic
500 for database errors. A conditional, parameterized update sets `deleted_at`
to the database timestamp and commits; failures roll back. Concurrent
deletions cannot both succeed.

The row and its ID remain in MySQL. Catalog, search, details, and update
exclude deleted rows; new reviews cannot be created for them. Existing
reviews retain their media title through an internal lookup, and related
reviews, ratings, favorites, comments, and tags are not deleted.

### Migration for existing databases

1. Back up the database and check the target and privileges with the database
   administrator. Configure `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`
   for that database using the same environment or local `.env` used by
   `backend/database.py`. Do not commit credentials. The migration account
   needs permission to inspect metadata and alter `media`.
2. From the repository root, run:

   ```powershell
   cd backend
   python migrate_media_soft_delete.py
   ```

3. Check the printed foreign-key constraints and success message. The script
   inspects media's incoming and outgoing foreign keys before adding a nullable
   `deleted_at` column with a NULL default. Existing rows remain visible.
   Run it again to verify it reports `deleted_at` already present.

MySQL DDL implicitly commits; the schema alteration cannot be rolled back as
part of an application transaction. If an incompatible `deleted_at` already
exists, the script stops without changing it: inspect and resolve it manually
after a backup. Existing non-NULL deletion timestamps are never cleared.
Fresh installations get the column directly from `schema.sql`.

The explicit seed never reactivates a soft-deleted seeded row or creates a
duplicate in its place. An unchanged seeded row remains deleted; if its
content differs from the original seed, the existing collision check stops
the seed without overwriting it. Seed is for initial setup, not an automatic
request-time operation or restore mechanism.

### GUI demonstration

1. As a manager, create a **new** `Sprint 5 Demo Movie`, type Movie, release
   year 2026, genre Adventure. Do not delete seeded IDs 1–5.
2. Search for the movie and open its details. Select **Delete Media**, check
   that the confirmation names the movie, and cancel.
3. Select **Delete Media** again and confirm. Check the success message, then
   use **Back to Search**.
4. Search for `Sprint 5 Demo Movie` and confirm there is no result. Reopen the
   previous details URL and confirm it displays `Media not found.`

Only managers see the control, and cancellation sends no DELETE. Failures
are displayed without claiming success. No restore interface is provided.
Reviews and other related data retain their existing storage behavior; in
particular, in-memory review state does not survive a backend restart.

### Validation

Local validation used a disposable MySQL 8.0.40 instance: 113 backend tests
and 187 repository Python tests passed, including Create, Read, Update, Delete,
rollback, review preservation, seed reruns, and concurrent deletion. A legacy
schema with an existing row and foreign key was migrated twice without losing
either. Eleven Node tests and all 50 Playwright browser tests passed (browser
suite uses mocked APIs). A separate live browser check created a new demo
movie, canceled and confirmed deletion, then verified search and details
after refresh and after restarting the isolated backend.