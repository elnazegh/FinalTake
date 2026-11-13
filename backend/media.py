from datetime import datetime
from urllib.parse import urlparse

VALID_MEDIA_TYPES = {"movie", "tv", "book", "game"}

MAX_TITLE_LENGTH = 255
MAX_GENRE_LENGTH = 100
MAX_IMAGE_URL_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 5000

MIN_RELEASE_YEAR = 1000
# Allow announced titles that have not been released yet.
RELEASE_YEAR_FUTURE_ALLOWANCE = 10


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


def clean_image_url(value):
    image_url = clean_optional_text(
        value, "imageUrl", MAX_IMAGE_URL_LENGTH
    )

    if image_url is None:
        return None

    # Only web URLs are accepted so stored values are safe to render.
    parsed = urlparse(image_url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("imageUrl must be a valid http or https URL.")

    return image_url


def validate_media_payload(data):
    """Validate a create-media request and return clean column values."""
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")

    title = data.get("title")
    media_type = data.get("type")
    release_year = data.get("releaseYear")

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

    if release_year is not None:
        # bool is a subclass of int, so it must be rejected explicitly.
        if isinstance(release_year, bool) or not isinstance(release_year, int):
            raise ValueError("releaseYear must be a whole number.")

        max_year = datetime.now().year + RELEASE_YEAR_FUTURE_ALLOWANCE

        if release_year < MIN_RELEASE_YEAR or release_year > max_year:
            raise ValueError(
                f"releaseYear must be between {MIN_RELEASE_YEAR} "
                f"and {max_year}."
            )

    return {
        "title": title,
        "media_type": media_type,
        "genre": clean_optional_text(
            data.get("genre"), "genre", MAX_GENRE_LENGTH
        ),
        "image_url": clean_image_url(data.get("imageUrl")),
        "release_year": release_year,
        "description": clean_optional_text(
            data.get("description"), "description", MAX_DESCRIPTION_LENGTH
        )
    }


def user_can_manage_media(connection, user_id):
    """Return True only for users listed in the media_managers table."""
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT 1 FROM media_managers WHERE user_id = %s",
            (user_id,)
        )

        return cursor.fetchone() is not None

    finally:
        cursor.close()


def create_media_record(connection, media_data):
    """Insert a media row and commit, rolling back on any failure."""
    cursor = connection.cursor()

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
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()

    return {
        "id": str(media_id),
        "title": media_data["title"],
        "type": media_data["media_type"],
        "genre": media_data["genre"],
        "imageUrl": media_data["image_url"],
        "releaseYear": media_data["release_year"],
        "description": media_data["description"]
    }
