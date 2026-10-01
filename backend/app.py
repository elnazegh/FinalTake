from flask import Flask, jsonify, request
from database import get_db_connection
from werkzeug.security import generate_password_hash
import re
from flask_cors import CORS

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://127.0.0.1:5500",
                "http://localhost:5500"
            ],
            "methods": ["GET", "POST", "OPTIONS"],
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

    return jsonify({
        "results": results
    }), 200

# --------------------------------------------------
# Future account routes
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

    except Exception as e:
        connection.rollback()

        if "Duplicate entry" in str(e):
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