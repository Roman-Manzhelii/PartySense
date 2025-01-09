from flask import Blueprint, jsonify, request, current_app
from services.user_service import UserService
from decorators.token_required import token_required
from bson.objectid import ObjectId
from marshmallow import Schema, fields, ValidationError
import logging

categories_bp = Blueprint('categories', __name__)
logger = logging.getLogger(__name__)

class CategoryCreateSchema(Schema):
    name = fields.String(required=True)
    description = fields.String(required=False, default="")

class AddPlaylistToCategorySchema(Schema):
    playlist_id = fields.String(required=True)

category_create_schema = CategoryCreateSchema()
add_playlist_schema = AddPlaylistToCategorySchema()

@categories_bp.route("/api/categories", methods=["POST"])
@token_required
def create_new_category(current_user):
    data = request.get_json()
    try:
        validated_data = category_create_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    name = validated_data.get("name")
    description = validated_data.get("description", "")

    user_id = str(current_user["_id"])
    user_service: UserService = current_app.user_service
    user_service.create_category(user_id, name, description)
    logger.info(f"Created new category '{name}' for user {user_id}.")

    return jsonify({"message": "Category created successfully."}), 201

@categories_bp.route("/api/categories", methods=["GET"])
@token_required
def get_user_categories(current_user):
    user_id = str(current_user["_id"])
    user_service: UserService = current_app.user_service
    categories = user_service.get_categories(user_id)
    categories_list = []
    for cat in categories:
        cat_dict = {
            "name": cat["name"],
            "description": cat.get("description", ""),
            "playlists": [str(pl_id) for pl_id in cat.get("playlists", [])]
        }
        categories_list.append(cat_dict)

    return jsonify({"categories": categories_list}), 200

@categories_bp.route("/api/categories/<category_name>/playlists", methods=["POST"])
@token_required
def add_playlist_to_category_route(current_user, category_name):
    data = request.get_json()
    try:
        validated_data = add_playlist_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    playlist_id = ObjectId(validated_data.get("playlist_id"))
    user_id = str(current_user["_id"])
    user_service: UserService = current_app.user_service

    user_service.add_playlist_to_category(user_id, category_name, playlist_id)
    logger.info(f"Added playlist {playlist_id} to category '{category_name}' for user {user_id}.")

    return jsonify({"message": "Playlist added to category successfully."}), 200
