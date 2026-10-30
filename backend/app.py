from flask import Flask, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import re
import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

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

app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("SESSION_COOKIE_SECURE", "false").lower()
    == "true"
)

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

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
    },
    supports_credentials=True
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
    current_user_id = session.get("user_id")

    if current_user_id is None:
        return jsonify({
            "error": "Authentication required."
        }), 401

    data = request.get_json(silent=True) or {}

    media_id = data.get("media_id")
    rating = data.get("rating")
    text = data.get("text")

    if (
        media_id is None
        or rating is None
        or text is None
    ):
        return jsonify({
            "error": (
                "media_id, rating, and text are required."
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
            user_id=current_user_id,
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
    current_user_id = session.get("user_id")

    if current_user_id is None:
        return jsonify({
            "error": "Authentication required."
        }), 401

    review = reviews.get(review_id)

    if review is None:
        return jsonify({
            "error": "Review not found."
        }), 404

    data = request.get_json(silent=True) or {}

    text = data.get("text")

    if text is None:
        return jsonify({
            "error": "text is required."
        }), 400

    try:
        review.edit_review(
            user_id=current_user_id,
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
    current_user_id = session.get("user_id")

    if current_user_id is None:
        return jsonify({
            "error": "Authentication required."
        }), 401
    review = reviews.get(review_id)

    if review is None:
        return jsonify({
            "error": "Review not found."
        }), 404

    try:
        review.delete_review(current_user_id)

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
    if not app.config.get("SECRET_KEY"):
        return jsonify({
            "error": "Authentication is not configured"
        }), 503

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required"
        }), 400

    identity = data.get("email") or data.get("username")
    password = data.get("password")

    if (
        not isinstance(identity, str)
        or not identity.strip()
        or not isinstance(password, str)
        or not password
    ):
        return jsonify({
            "error": "Email or username and password are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id, username, email, password_hash "
            "FROM users "
            "WHERE email = %s OR username = %s "
            "LIMIT 1",
            (identity.strip(), identity.strip())
        )

        user = cursor.fetchone()

    except Exception:
        return jsonify({
            "error": "Authentication service unavailable"
        }), 503

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

    if not user or not check_password_hash(
        user["password_hash"], password
    ):
        session.clear()

        return jsonify({
            "error": "Invalid credentials"
        }), 401

    session.clear()

    session["user_id"] = user["user_id"]
    session.permanent = False

    return jsonify({
        "message": "Login successful",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"]
        }
    }), 200


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "message": "Logout successful"
    }), 200

@app.route("/api/auth/session", methods=["GET"])
def auth_session():
    user_id = session.get("user_id")

    if user_id is None:
        return jsonify({
            "authenticated": False
        }), 401

    return jsonify({
        "authenticated": True,
        "user_id": user_id
    }), 200


# Sprint 4 - Send Password Reset Email

def send_password_reset_email(email, reset_token):
    # Get email settings from .env
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM")

    frontend_url = os.getenv(
        "FRONTEND_BASE_URL",
        "http://127.0.0.1:5500"
    )

    # Create the password reset link
    reset_link = (
        f"{frontend_url.rstrip('/')}/pages/reset-password.html?"
        f"{urlencode({'token': reset_token})}"
    )

    # Create the email
    message = EmailMessage()
    message["Subject"] = "FinalTake - Password Reset"
    message["From"] = smtp_from
    message["To"] = email

    message.set_content(
        "You requested a password reset for your FinalTake account.\n\n"
        f"Click the link below to reset your password:\n{reset_link}\n\n"
        "This link expires in 15 minutes and can only be used once.\n\n"
        "If you did not request this reset, you can ignore this email."
    )

    # Connect securely to the SMTP server
    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(smtp_username, smtp_password)
        server.send_message(message)

    return True


@app.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True)

    # Check if the request contains JSON data
    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid request"
        }), 400

    # Get the email entered by the user
    email = data.get("email")

    # Check if an email was provided
    if not isinstance(email, str) or not email.strip():
        return jsonify({
            "error": "Email is required"
        }), 400

    email = email.strip()

    connection = None
    cursor = None

    try:
        # Connect to MySQL
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check if the email exists
        cursor.execute(
            "SELECT user_id, email FROM users WHERE email = %s LIMIT 1",
            (email,)
        )

        user = cursor.fetchone()


        if user:
            # Generate a secure random token
            reset_token = secrets.token_urlsafe(32)

            # Hash the token before storing it
            token_hash = hashlib.sha256(
                reset_token.encode("utf-8")
            ).hexdigest()

            # Set expiration to 15 minutes (UTC)
            expires_at = (
                datetime.now(timezone.utc)
                + timedelta(minutes=15)
            ).replace(tzinfo=None)

            # Remove any previous reset tokens for this user
            cursor.execute(
                "DELETE FROM password_reset_tokens WHERE user_id = %s",
                (user["user_id"],)
            )

            # Save the new token hash and expiration time
            cursor.execute(
                """
                INSERT INTO password_reset_tokens
                (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user["user_id"], token_hash, expires_at)
            )


            # Save the reset token to MySQL
            connection.commit()

            # Send the reset link to the user's email
            send_password_reset_email(
                user["email"],
                reset_token
            )

            print("Password reset email sent successfully")



    except Exception:
        app.logger.exception("Password recovery database operation failed")

        if connection is not None:
            connection.rollback()

        return jsonify({
            "error": "Password recovery service unavailable"
        }), 503


    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

    # Do not reveal whether the account exists
    return jsonify({
        "message": "If an account exists for this email, password reset instructions will be sent."
    }), 200


@app.route("/api/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True)

    # Check request data
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request"}), 400

    token = data.get("token")
    new_password = data.get("password")

    # Validate token
    if not isinstance(token, str) or not token or len(token) > 256:
        return jsonify({"error": "Invalid reset token"}), 400

    # Validate new password
    if not isinstance(new_password, str) or len(new_password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    # Hash token to compare with MySQL
    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Find the token and lock it during the reset
        cursor.execute(
            """
            SELECT user_id, expires_at
            FROM password_reset_tokens
            WHERE token_hash = %s
            FOR UPDATE
            """,
            (token_hash,)
        )

        record = cursor.fetchone()

        # Compare against current UTC time
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        if not record or record["expires_at"] <= current_time:
            connection.rollback()
            return jsonify({
                "error": "Reset token is invalid or expired"
            }), 400

        # Hash the new password
        password_hash = generate_password_hash(new_password)

        # Update the user's password
        cursor.execute(
            """
            UPDATE users
            SET password_hash = %s
            WHERE user_id = %s
            """,
            (password_hash, record["user_id"])
        )

        # Delete all reset tokens for this user
        cursor.execute(
            "DELETE FROM password_reset_tokens WHERE user_id = %s",
            (record["user_id"],)
        )

        # Save both changes together
        connection.commit()

        # Clear the current browser session
        session.clear()

        return jsonify({
            "message": "Password reset successful"
        }), 200

    except Exception:
        app.logger.exception("Password reset failed")

        if connection is not None:
            connection.rollback()

        return jsonify({
            "error": "Password reset service unavailable"
        }), 503

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# --------------------------------------------------
# Start Flask server
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)