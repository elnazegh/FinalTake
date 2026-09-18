# Sprint 1 Merge Summary

## Source of truth
The uploaded `sprint-1-stuff.zip` was used as the current team version. Existing team files (`app.py`, `database.py`, `rating.py`, `review.py`, demo code, frontend, and dependency list) were preserved.

## Implemented in this merge
- Registered media API routes with the team's existing Flask application.
- Added a MySQL-backed media repository.
- Added media catalog endpoint (`GET /api/media`).
- Added media search endpoint (`GET /api/media/search?q=...`).
- Added media details with aggregate rating and reviews (`GET /api/media/<id>`).
- Added media creation endpoint (`POST /api/media`).
- Added MySQL schema for users, media, and reviews plus seed media.
- Reconciled the schema with the team's new half-star Rating model: ratings use DECIMAL(2,1), 0.5 through 5.0.
- Preserved the team's auth placeholders for future work.

## Files added
- `backend/media_repository.py`
- `backend/media_routes.py`
- `backend/sql/schema.sql`
- `backend/sql/seed.sql`
- `backend/.env.example`
- `deliverables/*`

## Files modified
- `backend/app.py` only to import/register the media blueprint.

## Intentionally not overwritten
- `backend/database.py`
- `backend/rating.py`
- `backend/review.py`
- `backend/requirements.txt`
- frontend and demo work
