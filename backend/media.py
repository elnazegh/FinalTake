VALID_MEDIA_TYPES = {"movie", "tv", "book", "game"}

MAX_TITLE_LENGTH = 255
MAX_GENRE_LENGTH = 100
MAX_IMAGE_URL_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 5000

MEDIA_COLUMNS = """
    media_id,
    title,
    media_type,
    genre,
    image_url,
    release_year,
    description
"""

# Whitelisted so the clause can be placed in SQL safely.
SORT_ORDERS = {
    "title_asc": "title ASC, media_id ASC",
    "title_desc": "title DESC, media_id ASC",
    "year_asc": "release_year ASC, title ASC",
    "year_desc": "release_year DESC, title ASC"
}

DEFAULT_SORT_ORDER = "media_id ASC"


def normalize_media_id(value):
    """Return a positive int media id, or None if the value is not one."""
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value if value > 0 else None

    if isinstance(value, str) and value.isascii() and value.isdigit():
        media_id = int(value)
        return media_id if media_id > 0 else None

    return None


def clean_optional_text(value, field_name, max_length):
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text.")

    value = value.strip()

    if not value:
        return None

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} cannot exceed {max_length} characters."
        )

    return value


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
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")

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

    title = title.strip()

    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(
            f"title cannot exceed {MAX_TITLE_LENGTH} characters."
        )

    if not isinstance(media_type, str) or not media_type.strip():
        raise ValueError("type is required.")

    media_type = media_type.strip().casefold()

    if media_type not in VALID_MEDIA_TYPES:
        raise ValueError("type must be movie, tv, book, or game.")

    if release_year in ("", None):
        release_year = None

    # bool is a subclass of int, so it must be rejected explicitly.
    elif isinstance(release_year, bool) or not isinstance(release_year, int):
        raise ValueError("releaseYear must be a number.")

    if release_year is not None and (
        release_year < 0 or release_year > 9999
    ):
        raise ValueError("releaseYear must be between 0 and 9999.")

    return {
        "title": title,
        "media_type": media_type,
        "genre": clean_optional_text(
            genre, "genre", MAX_GENRE_LENGTH
        ),
        "image_url": clean_optional_text(
            image_url, "imageUrl", MAX_IMAGE_URL_LENGTH
        ),
        "release_year": release_year,
        "description": clean_optional_text(
            description, "description", MAX_DESCRIPTION_LENGTH
        )
    }


def list_media(connection):
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            f"""
            SELECT {MEDIA_COLUMNS}
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


def escape_like(value):
    """Escape LIKE wildcards; pairs with ESCAPE '!' in the query."""
    return (
        value
        .replace("!", "!!")
        .replace("%", "!%")
        .replace("_", "!_")
    )


def search_media(
    connection,
    query,
    genre="",
    media_type="",
    sort=""
):
    conditions = ["LOWER(title) LIKE LOWER(%s) ESCAPE '!'"]
    parameters = [f"%{escape_like(query)}%"]

    if genre:
        conditions.append("LOWER(genre) = LOWER(%s)")
        parameters.append(genre)

    if media_type:
        conditions.append("LOWER(media_type) = LOWER(%s)")
        parameters.append(media_type)

    order_by = SORT_ORDERS.get(sort, DEFAULT_SORT_ORDER)
    where_clause = " AND ".join(conditions)

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            f"""
            SELECT {MEDIA_COLUMNS}
            FROM media
            WHERE {where_clause}
            ORDER BY {order_by}
            """,
            tuple(parameters)
        )

        return [
            serialize_media(row)
            for row in cursor.fetchall()
        ]

    finally:
        cursor.close()


def get_media(connection, media_id):
    media_id = normalize_media_id(media_id)

    if media_id is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            f"""
            SELECT {MEDIA_COLUMNS}
            FROM media
            WHERE media_id = %s
            """,
            (media_id,)
        )

        return serialize_media(cursor.fetchone())

    finally:
        cursor.close()


def create_media_record(connection, media_data):
    try:
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

            media_id = cursor.lastrowid

        finally:
            cursor.close()

        media = get_media(connection, media_id)

        if media is None:
            raise RuntimeError(
                "Inserted media row could not be read back."
            )

        connection.commit()

        return media

    except Exception:
        connection.rollback()
        raise
