from datetime import date, datetime
from flask import Blueprint, jsonify, request
from media_repository import MediaRepository

media_api = Blueprint("media_api", __name__)
VALID_MEDIA_TYPES = {"movie", "tv", "book", "game"}


def serialize(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialize(v) for v in value]
    return value


def bounded_int(raw, default, minimum, maximum):
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(value, maximum))


@media_api.get("/media")
def list_media():
    media_type = request.args.get("type")
    if media_type and media_type not in VALID_MEDIA_TYPES:
        return jsonify({"error": "invalid_media_type"}), 400
    limit = bounded_int(request.args.get("limit"), 20, 1, 100)
    offset = bounded_int(request.args.get("offset"), 0, 0, 100000)
    items = MediaRepository.list_media(media_type, limit, offset)
    return jsonify({"items": serialize(items), "limit": limit, "offset": offset})


@media_api.get("/media/search")
def search_media():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "missing_query", "message": "q is required"}), 400
    media_type = request.args.get("type")
    if media_type and media_type not in VALID_MEDIA_TYPES:
        return jsonify({"error": "invalid_media_type"}), 400
    limit = bounded_int(request.args.get("limit"), 20, 1, 100)
    return jsonify({"items": serialize(MediaRepository.search_media(query, media_type, limit)), "query": query})


@media_api.get("/media/<int:media_id>")
def media_details(media_id):
    item = MediaRepository.get_media(media_id)
    if not item:
        return jsonify({"error": "media_not_found"}), 404
    item = serialize(item)
    item["reviews"] = serialize(MediaRepository.get_reviews(media_id))
    return jsonify(item)


@media_api.post("/media")
def add_media():
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    media_type = str(payload.get("media_type", "")).strip().lower()
    if not title:
        return jsonify({"error": "validation_error", "message": "title is required"}), 400
    if media_type not in VALID_MEDIA_TYPES:
        return jsonify({"error": "validation_error", "message": "media_type must be movie, tv, book, or game"}), 400
    clean = {"title": title, "media_type": media_type, "description": payload.get("description"),
             "release_date": payload.get("release_date"), "creator": payload.get("creator"),
             "image_url": payload.get("image_url")}
    return jsonify(serialize(MediaRepository.create_media(clean, payload.get("created_by")))), 201
