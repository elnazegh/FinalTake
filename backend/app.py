from flask import Flask, jsonify, request
from database import get_db_connection


app = Flask(__name__)

media_items = [
    {
        "id": "1",
        "title": "The Dark Knight",
        "type": "movie",
        "imageUrl": None,
        "releaseYear": 2008
    },
    {
        "id": "2",
        "title": "Dark",
        "type": "tv",
        "imageUrl": None,
        "releaseYear": 2017
    },
    {
        "id": "3",
        "title": "Darkest Hour",
        "type": "movie",
        "imageUrl": None,
        "releaseYear": 2017
    },
    {
        "id": "4",
        "title": "Dune",
        "type": "book",
        "imageUrl": None,
        "releaseYear": 1965
    },
    {
        "id": "5",
        "title": "Dark Souls",
        "type": "game",
        "imageUrl": None,
        "releaseYear": 2011
    }
]

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1:5500"
    return response

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

    if not query:
        return jsonify({
            "results": []
        }), 200

    normalized_query = query.casefold()

    results = [
        media
        for media in media_items
        if normalized_query in media["title"].casefold()
    ]

    return jsonify({
        "results": results
    }), 200

# --------------------------------------------------
# Future account routes
# --------------------------------------------------

@app.route("/api/auth/register", methods=["POST"])
def register():
    return jsonify({
        "message": "Registration endpoint - not implemented yet"
    }), 501


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