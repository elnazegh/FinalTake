# Media Catalog Management - Create Media

This change adds the Create operation only. Read, Update and Delete are
delivered in separate pull requests.

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

## Known limitation until Read Media (PR 2)

Search (`GET /api/search`) and media details (`GET /api/media/<id>`) still read
the hardcoded in-memory catalog in `backend/app.py`. They do not read the
`media` table yet, so newly created media is stored in MySQL but does not
appear in search results or on a details page. For the same reason the form
confirms creation and shows the new media ID instead of redirecting to a
details page. Database-backed Read will be added in PR 2.

Notes for the next PRs:

- Created IDs start at 1 and can numerically overlap the hardcoded demo items
  (IDs 1 to 5). PR 2 should seed or migrate those items when switching reads
  to MySQL.
- API IDs are strings (for example `"7"`) to match the existing catalog, while
  the column is `INT AUTO_INCREMENT`.
- Reviews are still held in memory and refer to media by ID. PR 4 (Delete)
  should decide how reviews of a deleted item are handled.
- `image_url` is validated as http or https on write. Pages that render it
  should still treat it as untrusted.