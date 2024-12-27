from flask import Blueprint, jsonify, request, current_app
from services.user_service import UserService
from decorators.token_required import token_required
from marshmallow import Schema, fields, ValidationError
import logging

favorites_bp = Blueprint('favorites', __name__)
logger = logging.getLogger(__name__)

class FavoriteSchema(Schema):
    video_id = fields.String(required=True)
    title = fields.String(required=True)
    thumbnail_url = fields.String(required=True)
    duration = fields.Integer(required=True)
    added_at = fields.DateTime(required=False)

favorite_schema = FavoriteSchema()

@favorites_bp.route("/api/favorites", methods=["POST"])
@token_required
def add_favorite_song(current_user):
    data = request.get_json()
    try:
        validated_data = favorite_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    user_id = str(current_user["google_id"])  # Використовуємо google_id
    user_service: UserService = current_app.user_service
    user_service.add_favorite(user_id, validated_data)
    logger.info(f"Added song {validated_data['video_id']} to favorites for user {user_id}.")

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
