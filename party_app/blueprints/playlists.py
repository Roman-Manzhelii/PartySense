# blueprints/playlists.py
from flask import Blueprint, jsonify, request, current_app
from services.user_service import UserService
from decorators.token_required import token_required
from bson.objectid import ObjectId
from marshmallow import Schema, fields, ValidationError
import logging

playlists_bp = Blueprint('playlists', __name__)
logger = logging.getLogger(__name__)

# Схеми валідації
class PlaylistCreateSchema(Schema):
    name = fields.String(required=True)
    description = fields.String(required=False, default="")

class PlaylistUpdateSchema(Schema):
    name = fields.String(required=False)
    description = fields.String(required=False)
    songs = fields.List(fields.Dict(), required=False)

playlist_create_schema = PlaylistCreateSchema()
playlist_update_schema = PlaylistUpdateSchema()

@playlists_bp.route("/api/playlists", methods=["POST"])
@token_required
def create_new_playlist(current_user):
    data = request.get_json()
    try:
        validated_data = playlist_create_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    name = validated_data.get("name")
    description = validated_data.get("description", "")

    user_id = str(current_user["_id"])
    user_service: UserService = current_app.user_service
    playlist_id = user_service.create_playlist(user_id, name, description)
    logger.info(f"Created new playlist {playlist_id} for user {user_id}.")

    return jsonify({"message": "Playlist created successfully.", "playlist_id": str(playlist_id)}), 201

@playlists_bp.route("/api/playlists/<playlist_id>", methods=["PUT"])
@token_required
def update_existing_playlist(current_user, playlist_id):
    data = request.get_json()
    try:
        validated_data = playlist_update_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    user_id = str(current_user["_id"])
    user_service: UserService = current_app.user_service

    # Перевірка, чи належить плейлист користувачу
    playlist = user_service.get_playlists(user_id).filter({"_id": ObjectId(playlist_id)}).first()
    if not playlist:
        return jsonify({"error": "Playlist not found."}), 404

    update_data = {}
    if "name" in validated_data:
        update_data["name"] = validated_data["name"]
    if "description" in validated_data:
        update_data["description"] = validated_data["description"]
    if "songs" in validated_data:
        update_data["songs"] = validated_data["songs"]

    if not update_data:
        return jsonify({"error": "No valid fields to update."}), 400

    user_service.update_playlist(ObjectId(playlist_id), update_data)
    logger.info(f"Updated playlist {playlist_id} for user {user_id}.")

    return jsonify({"message": "Playlist updated successfully."}), 200

@playlists_bp.route("/api/playlists", methods=["GET"])
@token_required
def get_user_playlists(current_user):
    user_id = str(current_user["_id"])
    user_service: UserService = current_app.user_service
    playlists = user_service.get_playlists(user_id)
    playlists_list = []
    for pl in playlists:
        pl_dict = {
            "playlist_id": str(pl["_id"]),
            "name": pl["name"],
            "description": pl.get("description", ""),
            "songs": pl.get("songs", []),
            "created_at": pl["created_at"].isoformat(),
            "updated_at": pl["updated_at"].isoformat()
        }
        playlists_list.append(pl_dict)

    return jsonify({"playlists": playlists_list}), 200

@playlists_bp.route("/api/playlists/<playlist_id>", methods=["DELETE"])
@token_required
def delete_user_playlist(current_user, playlist_id):
    user_id = str(current_user["_id"])
    user_service: UserService = current_app.user_service
    success = user_service.delete_playlist(user_id, ObjectId(playlist_id))
    if success:
        logger.info(f"Deleted playlist {playlist_id} for user {user_id}.")
        return jsonify({"message": "Playlist deleted successfully."}), 200
    else:
        logger.error(f"Failed to delete playlist {playlist_id} for user {user_id}.")
        return jsonify({"error": "Failed to delete playlist."}), 500
