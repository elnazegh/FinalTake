from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash
from flask_cors import CORS
import re

# These imports support both running app.py directly
# and importing backend.app from the automated tests.
try:
    from .database import get_db_connection
    from .media import create_media_record
    from .media import get_media
    from .media import list_media
    from .media import normalize_media_id
    from .media import search_media
    from .media import validate_media_payload
    from .rating import Rating
    from .review import Review
except ImportError:
    from database import get_db_connection
    from media import create_media_record
    from media import get_media
    from media import list_media
    from media import normalize_media_id
    from media import search_media
    from media import validate_media_payload
    from rating import Rating
    from review import Review


app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://127.0.0.1:5500",
                "http://localhost:5500"
            ],
            "methods": [
                "GET",
                "POST",
                "PATCH",
                "DELETE",
                "OPTIONS"
            ],
            "allow_headers": ["Content-Type"]
        }
    }
)


# Temporary in-memory review storage until
# database review persistence is available.
reviews = {}
next_review_id = 1


class MediaLookupError(Exception):
    """The media catalog could not be read from the database."""


@app.errorhandler(MediaLookupError)
def handle_media_lookup_error(error):
    return jsonify({
        "error": "Unable to load media catalog."
    }), 500


def load_media_titles(media_ids):
    """Map media id strings to titles using the database catalog."""
    titles = {}

    if not media_ids:
        return titles

    try:
        connection = get_db_connection()

        try:
            for media_id in set(media_ids):
                media = get_media(connection, media_id)

                if media is not None:
                    titles[str(media_id)] = media["title"]

        finally:
            connection.close()

    except Exception as error:
        raise MediaLookupError() from error

    return titles


def serialize_review(review_id, review, media_titles):
    """Convert a Review object into API response data."""
    review_data = review.to_dict()

    if review_data is None:
        return None

    return {
        "id": review_id,
        **review_data,
        "media_title": media_titles.get(str(review.media_id))
    }


# --------------------------------------------------
# Basic backend route
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "FinalTake backend is running"
    }), 200


# --------------------------------------------------
# Health check route
# --------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    try:
        connection = get_db_connection()

        if connection.is_connected():
            connection.close()

            return jsonify({
                "status": "healthy",
                "database": "connected"
            }), 200

        return jsonify({
            "status": "unhealthy",
            "database": "disconnected"
        }), 500

    except Exception as error:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(error)
        }), 500


# --------------------------------------------------
# Media routes
# --------------------------------------------------

@app.route("/api/media", methods=["GET"])
def get_media_catalog():
    try:
        connection = get_db_connection()

        try:
            media = list_media(connection)

        finally:
            connection.close()

    except Exception:
        return jsonify({
            "error": "Unable to load media catalog."
        }), 500

    return jsonify({
        "media": media
    }), 200


@app.route("/api/media/<int:media_id>", methods=["GET"])
def get_media_details(media_id):
    try:
        connection = get_db_connection()

        try:
            media = get_media(connection, media_id)

        finally:
            connection.close()

    except Exception:
        return jsonify({
            "error": "Unable to load media item."
        }), 500

    if media is None:
        return jsonify({
            "error": "Media not found."
        }), 404

    # The frontend reads the media object directly, not wrapped.
    return jsonify(media), 200


@app.route("/api/media", methods=["POST"])
def create_media():
    data = request.get_json(silent=True)

    try:
        media_data = validate_media_payload(data)

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    try:
        connection = get_db_connection()

        try:
            media = create_media_record(
                connection,
                media_data
            )

        finally:
            connection.close()

    except Exception:
        return jsonify({
            "error": "Unable to create media item."
        }), 500

    return jsonify({
        "media": media
    }), 201


# --------------------------------------------------
# Search route
# --------------------------------------------------

@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("query", "").strip()
    genre = request.args.get("genre", "").strip()
    media_type = request.args.get("media_type", "").strip()
    sort = request.args.get("sort", "").strip()

    if not query:
        return jsonify({
            "results": []
        }), 200

    try:
        connection = get_db_connection()

        try:
            results = search_media(
                connection,
                query,
                genre,
                media_type,
                sort
            )

        finally:
            connection.close()

    except Exception:
        return jsonify({
            "error": "Unable to search media catalog."
        }), 500

    return jsonify({
        "results": results
    }), 200


# --------------------------------------------------
# Review routes
# --------------------------------------------------

@app.route("/api/reviews", methods=["POST"])
def create_review():
    global next_review_id

    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    media_id = data.get("media_id")
    rating = data.get("rating")
    text = data.get("text")

    if (
        user_id is None
        or media_id is None
        or rating is None
        or text is None
    ):
        return jsonify({
            "error": (
                "user_id, media_id, rating, and text are required."
            )
        }), 400

    media_id = normalize_media_id(media_id)
    media_titles = (
        load_media_titles([media_id])
        if media_id is not None
        else {}
    )

    if str(media_id) not in media_titles:
        return jsonify({
            "error": "Media item not found."
        }), 404

    if not Rating.is_valid_rating(rating):
        return jsonify({
            "error": (
                "Rating must be between 0.5 and 5.0 "
                "in half-star increments."
            )
        }), 400

    try:
        review = Review(
            user_id=user_id,
            media_id=str(media_id),
            rating=float(rating),
            text=text
        )

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    review_id = next_review_id
    next_review_id += 1

    reviews[review_id] = review

    return jsonify({
        "review": serialize_review(
            review_id,
            review,
            media_titles
        )
    }), 201


@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    media_id = request.args.get("media_id")

    selected = [
        (review_id, review)
        for review_id, review in reviews.items()
        if media_id is None or str(review.media_id) == str(media_id)
    ]

    media_titles = load_media_titles(
        [review.media_id for _, review in selected]
    )

    results = []

    for review_id, review in selected:
        review_data = serialize_review(
            review_id,
            review,
            media_titles
        )

        if review_data is not None:
            results.append(review_data)

    return jsonify({
        "reviews": results
    }), 200


@app.route("/api/reviews/<int:review_id>", methods=["GET"])
def get_review(review_id):
    review = reviews.get(review_id)

    if review is None:
        return jsonify({
            "error": "Review not found."
        }), 404

    media_titles = load_media_titles([review.media_id])

    return jsonify({
        "review": serialize_review(
            review_id,
            review,
            media_titles
        )
    }), 200


@app.route("/api/reviews/<int:review_id>", methods=["PATCH"])
def update_review(review_id):
    review = reviews.get(review_id)

    if review is None:
        return jsonify({
            "error": "Review not found."
        }), 404

    media_titles = load_media_titles([review.media_id])

    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    text = data.get("text")

    if user_id is None or text is None:
        return jsonify({
            "error": "user_id and text are required."
        }), 400

    try:
        review.edit_review(
            user_id=user_id,
            new_text=text
        )

    except PermissionError as error:
        return jsonify({
            "error": str(error)
        }), 403

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    return jsonify({
        "review": serialize_review(
            review_id,
            review,
            media_titles
        )
    }), 200


@app.route("/api/reviews/<int:review_id>", methods=["DELETE"])
def remove_review(review_id):
    review = reviews.get(review_id)

    if review is None:
        return jsonify({
            "error": "Review not found."
        }), 404

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")

    if user_id is None:
        return jsonify({
            "error": "user_id is required."
        }), 400

    try:
        review.delete_review(user_id)

    except PermissionError as error:
        return jsonify({
            "error": str(error)
        }), 403

    del reviews[review_id]

    return jsonify({
        "message": "Review deleted."
    }), 200


# --------------------------------------------------
# Account routes
# --------------------------------------------------

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username:
        return jsonify({
            "error": "Username is required"
        }), 400

    if not email:
        return jsonify({
            "error": "Email is required"
        }), 400

    if not password:
        return jsonify({
            "error": "Password is required"
        }), 400

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.match(email_pattern, email):
        return jsonify({
            "error": "Invalid email format"
        }), 400

    hashed_password = generate_password_hash(
        password,
        method="pbkdf2:sha256"
    )

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (username, email, hashed_password)
        )

        connection.commit()

    except Exception as error:
        connection.rollback()

        if "Duplicate entry" in str(error):
            return jsonify({
                "error": "Username or email already exists"
            }), 409

        return jsonify({
            "error": "Registration failed"
        }), 500

    finally:
        cursor.close()
        connection.close()

    return jsonify({
        "message": "User registered successfully"
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    return jsonify({
        "message": "Login endpoint - not implemented yet"
    }), 501


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    return jsonify({
        "message": "Logout endpoint - not implemented yet"
    }), 501


@app.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    return jsonify({
        "message": "Password recovery endpoint - not implemented yet"
    }), 501


# --------------------------------------------------
# Start Flask server
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
