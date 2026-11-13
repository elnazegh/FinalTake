# Media Catalog Management - Create Media

Create and Read are delivered as separate pull requests. Update and Delete
remain out of scope.

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
frontend can show or hide the Add Media link. It only reports the current
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
normal application request.

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