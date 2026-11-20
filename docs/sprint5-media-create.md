# Media Catalog Management - Create Media

Create, Read, and Update are delivered as separate pull requests. Delete
remains out of scope.

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
`password_reset_tokens` or any existing rows. There is no migration tool, so
existing installations must run the file once, for example:

```
mysql -u <admin_user> -p <database_name> < backend/schema.sql
```

`-p` with no value makes the client prompt for the password, so it is not
stored in shell history or in any file.

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
for their current in-process references and existing tests. PR 4 (Delete)
should decide how reviews of deleted media are handled.

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