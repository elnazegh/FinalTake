"""Explicit, repeatable migration of the legacy demo media into MySQL."""

import sys

try:
    from .database import get_db_connection
except ImportError:
    from database import get_db_connection


DEMO_MEDIA = (
    {
        "media_id": 1,
        "title": "The Dark Knight",
        "media_type": "movie",
        "genre": "Action",
        "image_url": None,
        "release_year": 2008,
        "description": None
    },
    {
        "media_id": 2,
        "title": "Dark",
        "media_type": "tv",
        "genre": "Drama",
        "image_url": None,
        "release_year": 2017,
        "description": None
    },
    {
        "media_id": 3,
        "title": "Darkest Hour",
        "media_type": "movie",
        "genre": "Drama",
        "image_url": None,
        "release_year": 2017,
        "description": None
    },
    {
        "media_id": 4,
        "title": "Dune",
        "media_type": "book",
        "genre": "Science Fiction",
        "image_url": None,
        "release_year": 1965,
        "description": None
    },
    {
        "media_id": 5,
        "title": "Dark Souls",
        "media_type": "game",
        "genre": "RPG",
        "image_url": None,
        "release_year": 2011,
        "description": None
    }
)

MEDIA_COLUMNS = (
    "media_id",
    "title",
    "media_type",
    "genre",
    "image_url",
    "release_year",
    "description"
)


class MediaSeedConflict(Exception):
    """The database contains media that conflicts with a legacy demo ID."""


def _matches_demo_record(row, demo_record):
    return all(
        row[column] == demo_record[column]
        for column in MEDIA_COLUMNS
    )


def seed_demo_media(connection):
    """Insert missing legacy rows or fail before writes on any collision."""
    cursor = connection.cursor(dictionary=True)

    try:
        records_to_insert = []
        conflicts = []

        for demo_record in DEMO_MEDIA:
            cursor.execute(
                """
                SELECT media_id, title, media_type, genre, image_url,
                       release_year, description
                FROM media
                WHERE media_id = %s
                """,
                (demo_record["media_id"],)
            )
            existing = cursor.fetchone()

            if existing is not None:
                if not _matches_demo_record(existing, demo_record):
                    conflicts.append(
                        f"ID {demo_record['media_id']} is occupied by "
                        f"'{existing['title']}' ({existing['media_type']})"
                    )

            cursor.execute(
                """
                SELECT media_id, title, media_type
                FROM media
                WHERE title = %s AND media_type = %s
                """,
                (demo_record["title"], demo_record["media_type"])
            )
            same_title = [
                row for row in cursor.fetchall()
                if row["media_id"] != demo_record["media_id"]
            ]

            if same_title:
                ids = ", ".join(str(row["media_id"]) for row in same_title)
                conflicts.append(
                    f"'{demo_record['title']}' ({demo_record['media_type']}) "
                    f"already exists under ID(s) {ids}"
                )
            elif existing is None:
                records_to_insert.append(demo_record)

        if conflicts:
            raise MediaSeedConflict(
                "Demo media seed stopped without changing data: "
                + "; ".join(conflicts)
                + ". Back up the database and resolve the ID/title conflict "
                "manually before retrying."
            )

        for record in records_to_insert:
            cursor.execute(
                """
                INSERT INTO media (
                    media_id,
                    title,
                    media_type,
                    genre,
                    image_url,
                    release_year,
                    description
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                tuple(record[column] for column in MEDIA_COLUMNS)
            )

        connection.commit()
        return len(records_to_insert)

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()


def main():
    connection = None

    try:
        connection = get_db_connection()
        inserted = seed_demo_media(connection)
        print(f"Demo media seed complete. Inserted {inserted} record(s).")
        return 0

    except MediaSeedConflict as error:
        print(str(error), file=sys.stderr)
        return 1

    except Exception:
        print(
            "Unable to seed demo media. No changes were committed.",
            file=sys.stderr
        )
        return 1

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
