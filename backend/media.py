VALID_MEDIA_TYPES = {"movie", "tv", "book", "game"}


def clean_optional_text(value):
    if isinstance(value, str) and value.strip():
        return value.strip()

    return None


def serialize_media(row):
    if row is None:
        return None

    return {
        "id": str(row["media_id"]),
        "title": row["title"],
        "type": row["media_type"],
        "genre": row["genre"],
        "imageUrl": row["image_url"],
        "releaseYear": row["release_year"],
        "description": row["description"]
    }


def validate_media_payload(data):
    title = data.get("title")
    media_type = data.get("type") or data.get("media_type")
    genre = data.get("genre")
    image_url = data.get("imageUrl") or data.get("image_url")
    release_year = data.get("releaseYear")

    if release_year is None:
        release_year = data.get("release_year")
    description = data.get("description")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("title is required.")

    if not isinstance(media_type, str) or not media_type.strip():
        raise ValueError("type is required.")

    media_type = media_type.strip().casefold()

    if media_type not in VALID_MEDIA_TYPES:
        raise ValueError("type must be movie, tv, book, or game.")

    if release_year in ("", None):
        release_year = None

    elif not isinstance(release_year, int):
        raise ValueError("releaseYear must be a number.")

    if release_year is not None and (
        release_year < 0 or release_year > 9999
    ):
        raise ValueError("releaseYear must be between 0 and 9999.")

    return {
        "title": title.strip(),
        "media_type": media_type,
        "genre": clean_optional_text(genre),
        "image_url": clean_optional_text(image_url),
        "release_year": release_year,
        "description": clean_optional_text(description)
    }


def list_media(connection):
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                media_id,
                title,
                media_type,
                genre,
                image_url,
                release_year,
                description
            FROM media
            ORDER BY title ASC
            """
        )

        return [
            serialize_media(row)
            for row in cursor.fetchall()
        ]

    finally:
        cursor.close()


def get_media(connection, media_id):
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                media_id,
                title,
                media_type,
                genre,
                image_url,
                release_year,
                description
            FROM media
            WHERE media_id = %s
            """,
            (media_id,)
        )

        return serialize_media(cursor.fetchone())

    finally:
        cursor.close()


def create_media_record(connection, media_data):
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            INSERT INTO media (
                title,
                media_type,
                genre,
                image_url,
                release_year,
                description
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                media_data["title"],
                media_data["media_type"],
                media_data["genre"],
                media_data["image_url"],
                media_data["release_year"],
                media_data["description"]
            )
        )

        connection.commit()
        media_id = cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()

    return get_media(connection, media_id)
