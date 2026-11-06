
"""Authenticated API routes for following and unfollowing tags."""

from flask import Blueprint, jsonify, request, session

try:
    from .tag_follow import TagFollows, normalize_follow_tag
except ImportError:
    from tag_follow import TagFollows, normalize_follow_tag


tag_follow_bp = Blueprint("tag_follow", __name__)
tag_follows = TagFollows()


@tag_follow_bp.route("/api/tags/following", methods=["GET"])
def list_followed_tags():
    user_id = session.get("user_id")

    if user_id is None:
        return jsonify({
            "error": "Authentication required."
        }), 401

    return jsonify({
        "tags": tag_follows.get_followed_tags(user_id)
    }), 200


@tag_follow_bp.route("/api/tags/following", methods=["POST"])
def follow_tag():
    user_id = session.get("user_id")

    if user_id is None:
        return jsonify({
            "error": "Authentication required."
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required."
        }), 400

    try:
        normalized = normalize_follow_tag(data.get("tag"))
        created = tag_follows.follow(user_id, normalized)

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    return jsonify({
        "tag": normalized,
        "following": True,
        "created": created,
        "tags": tag_follows.get_followed_tags(user_id)
    }), 201 if created else 200


@tag_follow_bp.route(
    "/api/tags/following/<path:tag>",
    methods=["DELETE"]
)
def unfollow_tag(tag):
    user_id = session.get("user_id")

    if user_id is None:
        return jsonify({
            "error": "Authentication required."
        }), 401

    try:
        normalized = normalize_follow_tag(tag)
        removed = tag_follows.unfollow(user_id, normalized)

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    return jsonify({
        "tag": normalized,
        "following": False,
        "removed": removed,
        "tags": tag_follows.get_followed_tags(user_id)
    }), 200
