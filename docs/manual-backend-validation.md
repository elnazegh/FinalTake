# Manual Backend Validation Checklist (Sprint 3)

Status key: `Not executed` until a tester runs the case and records the result. Do not mark Pass/Fail without actually running it.

Setup used by all cases: backend running locally (`cd backend; python app.py`, default `http://127.0.0.1:5000`), a **test** MySQL database created from `backend/schema.sql` and referenced by `backend/.env` (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`). Never use the shared dev database for destructive cases. Jira keys are not known yet and are marked `TBD`.

| ID | Feature | Preconditions | Test data | Steps | Expected result | Actual result | Status | Jira |
|---|---|---|---|---|---|---|---|---|
| MB-01 | Health check, DB up | Backend running, DB reachable | None | `GET /api/health` | 200, `{"status":"healthy","database":"connected"}` | | Not executed | TBD |
| MB-02 | Health check, DB down | Backend running, MySQL stopped or wrong `DB_PASSWORD` | None | `GET /api/health` | 500, `status: unhealthy`, `database: disconnected` | | Not executed | TBD |
| MB-03 | Register valid user | Empty `users` table | `alice` / `alice@example.com` / `password123` | `POST /api/auth/register` with JSON body; then `SELECT * FROM users` | 201; one row; `password_hash` is not `password123` | | Not executed | TBD |
| MB-04 | Duplicate username | MB-03 done | `alice` / `other@example.com` / any | Repeat register | 409; still one row | | Not executed | TBD |
| MB-05 | Duplicate email | MB-03 done | `bob` / `alice@example.com` / any | Repeat register | 409; still one row | | Not executed | TBD |
| MB-06 | Missing username | None | Body without `username` | Register | 400 "Username is required"; no row | | Not executed | TBD |
| MB-07 | Missing email | None | Body without `email` | Register | 400 "Email is required"; no row | | Not executed | TBD |
| MB-08 | Missing password | None | Body without `password` | Register | 400 "Password is required"; no row | | Not executed | TBD |
| MB-09 | Empty request body | None | `{}` | Register | 400 "Request body is required"; no row | | Not executed | TBD |
| MB-10 | Invalid email format | None | `not-an-email`, `a@b`, `a b@c.com` | Register each | 400 "Invalid email format"; no rows | | Not executed | TBD |
| MB-11 | Over-length username | None | Username of 51 characters | Register | Non-success response (expected 500 "Registration failed"); no row | | Not executed | TBD |
| MB-12 | SQL metacharacters | Empty `users` table | Username `x'; DROP TABLE users; --` | Register; `SELECT * FROM users` | 201; table intact; username stored literally | | Not executed | TBD |
| MB-13 | Unicode username | None | `josé`, `用户` | Register; read row back | Stored and read back unchanged, or a clean error (record which) | | Not executed | TBD |
| MB-14 | Whitespace-only username | None | Username `"   "` | Register | Record behavior. Currently expected to be accepted (known gap). | | Not executed | TBD |
| MB-15 | Database outage during register | Backend running, MySQL stopped | Valid user | Register | 500 response, backend keeps running | | Not executed | TBD |
| MB-16 | DB constraints (direct SQL, test DB only) | Test DB | Insert duplicate `username`; insert `NULL` `email` | Run `INSERT` statements in a SQL client | Duplicate: error 1062. NULL: error 1048. Row count unchanged. | | Not executed | TBD |
| MB-17 | Media search, partial match | Backend running | `query=dark` | `GET /api/search?query=dark` | 200; 4 results (The Dark Knight, Dark, Darkest Hour, Dark Souls) | | Not executed | TBD |
| MB-18 | Media search, no result | Backend running | `query=zzzz` | `GET /api/search?query=zzzz` | 200, `{"results": []}` | | Not executed | TBD |
| MB-19 | Media search, empty query | Backend running | `query=` | `GET /api/search?query=` | 200, `{"results": []}` | | Not executed | TBD |
| MB-20 | Media by ID | Backend running | `1` | `GET /api/media/1` | 200, "The Dark Knight" | | Not executed | TBD |
| MB-21 | Media by invalid ID | Backend running | `999`, `0`, `-1`, `abc` | `GET /api/media/<id>` for each | 404 for each | | Not executed | TBD |
| MB-22 | Create review | Backend running | `user_id=1, media_id=1, rating=4.5, text="Great"` | `POST /api/reviews` | 201 with review and `media_title` | | Not executed | TBD |
| MB-23 | Review rating boundaries | Backend running | Ratings 0.5 and 5.0 (valid); 0, 0.4, 5.5 (invalid) | `POST /api/reviews` for each | 201 for valid; 400 for invalid | | Not executed | TBD |
| MB-24 | Review text boundary | Backend running | 5000 chars and 5001 chars | `POST /api/reviews` | 201 for 5000; 400 for 5001 | | Not executed | TBD |
| MB-25 | Edit/delete review, owner vs non-owner | MB-22 done; record the review ID | PATCH bodies: `{"user_id":2,"text":"Unauthorized edit"}` and `{"user_id":1,"text":"Updated"}`; DELETE bodies: `{"user_id":2}` and `{"user_id":1}` | On the recorded ID, PATCH and DELETE as user 2 first; GET to verify the review is unchanged; then PATCH and DELETE as user 1 | Non-owner: 403 and review unchanged. Owner: 200 for both operations. | | Not executed | TBD |
| MB-26 | Missing review | Backend running | ID `999` | `GET`, `PATCH`, `DELETE /api/reviews/999` | 404 "Review not found." | | Not executed | TBD |
| MB-27 | Review persistence (known limitation) | MB-22 done | None | Restart backend; `GET /api/reviews` | Reviews are in memory today, so the list is empty after restart | | Not executed | TBD |
