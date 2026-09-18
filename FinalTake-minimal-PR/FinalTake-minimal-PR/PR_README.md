# Minimal Pull Request Files

This package contains only files added or changed by the database/media backend work when compared with the uploaded Sprint 1 baseline.

## Existing file changed
- `backend/app.py` — adds the media API blueprint import and registration. The only code changes are two lines. `backend/app.py.patch` shows the exact diff.

## New code/config files
- `backend/.env.example`
- `backend/media_repository.py`
- `backend/media_routes.py`
- `backend/sql/schema.sql`
- `backend/sql/seed.sql`

## Non-code deliverables
- `deliverables/` contains the project/sprint documentation requested earlier.

## Do NOT copy an entire old project snapshot
Create your branch from the current target branch, then copy only the paths above into that checkout. Existing files such as `database.py`, `rating.py`, `review.py`, frontend files, demos, and `requirements.txt` are intentionally not included because they are unchanged from the Sprint 1 baseline.

After copying, run:

    git status
    git diff

Git should report only the new files plus the small `backend/app.py` modification.
