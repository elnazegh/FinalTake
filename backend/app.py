from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash
from flask_cors import CORS
import re

# These imports support both running app.py directly
# and importing backend.app from the automated tests.
try:
    from .database import get_db_connection
    from .rating import Rating
    from .review import Review
except ImportError:
    from database import get_db_connection
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


media_items = [
    {
        "id": "1",
        "title": "The Dark Knight",
        "type": "movie",
        "genre": "Action",
        "imageUrl": None,
        "releaseYear": 2008
    },
    {
        "id": "2",
        "title": "Dark",
        "type": "tv",
        "genre": "Drama",
        "imageUrl": None,
        "releaseYear": 2017
    },
    {
        "id": "3",
        "title": "Darkest Hour",
        "type": "movie",
        "genre": "Drama",
        "imageUrl": None,
        "releaseYear": 2017
    },
    {
        "id": "4",
        "title": "Dune",
        "type": "book",
        "genre": "Science Fiction",
        "imageUrl": None,
        "releaseYear": 1965
    },
    {
        "id": "5",
        "title": "Dark Souls",
        "type": "game",
        "genre": "RPG",
        "imageUrl": None,
        "releaseYear": 2011
    }
]


# Temporary in-memory review storage until
# database review persistence is available.
reviews = {}
next_review_id = 1


def get_media_by_id(media_id):
    """Find a media item using the shared media data."""
    media_id = str(media_id)

    for media in media_items:
        if media["id"] == media_id:
            return media

    return None


def serialize_review(review_id, review):
    """Convert a Review object into API response data."""
    review_data = review.to_dict()

    if review_data is None:
        return None

    media = get_media_by_id(review.media_id)

    return {
        "id": review_id,
        **review_data,
        "media_title": media["title"] if media else None
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

    normalized_query = query.casefold()
    normalized_genre = genre.casefold()
    normalized_media_type = media_type.casefold()

    results = [
        media
        for media in media_items
        if normalized_query in media["title"].casefold()
        and (
            not normalized_genre
            or media["genre"].casefold() == normalized_genre
        )
        and (
            not normalized_media_type
            or media["type"].casefold() == normalized_media_type
        )
    ]

    if sort == "title_asc":
        results.sort(
            key=lambda media: media["title"].casefold()
        )

    elif sort == "title_desc":
        results.sort(
            key=lambda media: media["title"].casefold(),
            reverse=True
        )

    elif sort == "year_desc":
        results.sort(
            key=lambda media: media["releaseYear"],
            reverse=True
        )

    elif sort == "year_asc":
        results.sort(
            key=lambda media: media["releaseYear"]
        )

    return jsonify({
        "results": results
    }), 200

@app.route("/api/media/<int:media_id>", methods=["GET"])
def get_media_details(media_id):
    media = get_media_by_id(media_id)

    if media is None:
        return jsonify({
            "error": "Media not found."
        }), 404

    return jsonify(media), 200


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

    media = get_media_by_id(media_id)

    if media is None:
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
            review
        )
    }), 201


@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    media_id = request.args.get("media_id")

    results = []

    for review_id, review in reviews.items():
        if media_id is not None:
            if str(review.media_id) != str(media_id):
                continue

        review_data = serialize_review(
            review_id,
            review
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

    return jsonify({
        "review": serialize_review(
            review_id,
            review
        )
    }), 200


@app.route("/api/reviews/<int:review_id>", methods=["PATCH"])
def update_review(review_id):
    review = reviews.get(review_id)

    if review is None:
        return jsonify({
            "error": "Review not found."
        }), 404

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
            review
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