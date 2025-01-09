from flask import Blueprint, jsonify, request, current_app
from services.user_service import UserService
from decorators.token_required import token_required
from marshmallow import Schema, fields, ValidationError
import logging
from datetime import datetime, timezone

from youtube_api import get_video_details

favorites_bp = Blueprint('favorites', __name__)
logger = logging.getLogger(__name__)

class FavoriteSchema(Schema):
    video_id = fields.String(required=True)
    title = fields.String(required=False)
    thumbnail_url = fields.String(required=False)
    duration = fields.Integer(required=False)
    added_at = fields.DateTime(required=False)

favorite_schema = FavoriteSchema()

@favorites_bp.route("/api/favorites", methods=["POST"])
@token_required
def add_favorite_song(current_user):
    data = request.get_json() or {}
    user_id = str(current_user["google_id"])
    user_service: UserService = current_app.user_service

    try:
        validated_data = favorite_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    video_id = validated_data["video_id"]

    details = get_video_details(video_id)
    if details:
        real_title = details["title"]
        real_thumb = details["thumbnail_url"]
        real_duration = details["duration_seconds"]
    else:
        real_title = validated_data.get("title", "Unknown Title")
        real_thumb = validated_data.get("thumbnail_url", "")
        real_duration = validated_data.get("duration", 0)

    now = datetime.now(timezone.utc)
    song_obj = {
        "video_id": video_id,
        "title": real_title,
        "thumbnail_url": real_thumb,
        "duration": real_duration,
        "added_at": now
    }

    user_service.add_favorite(user_id, song_obj)
    logger.info(f"Added song {video_id} to favorites for user {user_id}.")
    return jsonify({"message": "Song added to favorites."}), 201

@favorites_bp.route("/api/favorites/<video_id>", methods=["DELETE"])
@token_required
def remove_favorite_song(current_user, video_id):
    user_id = str(current_user["google_id"])
    user_service: UserService = current_app.user_service
    user_service.remove_favorite(user_id, video_id)
    logger.info(f"Removed song {video_id} from favorites for user {user_id}.")
    return jsonify({"message": "Song removed from favorites."}), 200

@favorites_bp.route("/api/favorites", methods=["GET"])
@token_required
def get_user_favorites(current_user):
    user_id = str(current_user["google_id"])
    user_service: UserService = current_app.user_service
    favorites = user_service.get_favorites(user_id)
    if favorites:
        favorites_list = favorites.get("songs", [])
        return jsonify({"favorites": favorites_list}), 200
    else:
        return jsonify({"favorites": []}), 200
