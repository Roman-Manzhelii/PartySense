from flask import Blueprint, jsonify, request, current_app
from services.user_service import UserService
from decorators.token_required import token_required
from marshmallow import Schema, fields, ValidationError
import logging
import traceback
from datetime import datetime, timezone

playback_bp = Blueprint('playback', __name__)
logger = logging.getLogger(__name__)

class PlayCommandSchema(Schema):
    action = fields.String(
        required=True,
        validate=lambda x: x in [
            "play", "pause", "resume", "next", "previous",
            "seek", "set_mode", "set_motion_detection"
        ]
    )
    video_id = fields.String(required=False)
    position = fields.Integer(required=False)
    mode = fields.String(required=False, validate=lambda x: x in ["repeat", "default", "shuffle"])
    enabled = fields.Boolean(required=False)

play_command_schema = PlayCommandSchema()

@playback_bp.route("/api/playback", methods=["POST"])
@token_required
def handle_playback(current_user):
    data = request.get_json()
    try:
        validated_data = play_command_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    action = validated_data.get("action")
    user_id = str(current_user["_id"])
    user_service: UserService = current_app.user_service
    pubnub_client = current_app.pubnub_client
    user_doc = user_service.get_user_by_google_id(current_user["google_id"])

    try:
        if action == "play":
            video_id = validated_data.get("video_id")
            position = validated_data.get("position", 0)
            mode = validated_data.get("mode", "default")
            if not video_id:
                return jsonify({"error": "video_id is required for play action."}), 400

            current_song = {
                "video_id": video_id,
                "title": "Unknown Title",
                "thumbnail_url": "http://example.com/image.jpg",
                "duration": 0,
                "position": position,
                "state": "playing",
                "mode": mode,
                "motion_detected": user_doc.get("preferences", {}).get("motion_detection", True),
                "updated_at": datetime.now(timezone.utc)
            }
            user_service.update_current_playback(user_id, current_song)

            command = {
                "action": "play",
                "video_id": video_id,
                "position": position,
                "mode": mode
            }
            success = pubnub_client.publish_message(user_doc['channel_name_commands'], command)
            if success:
                logger.info(f"Play command sent for user {user_id}.")
                return jsonify({"message": "Play command sent."}), 200
            else:
                return jsonify({"error": "Failed to send play command."}), 500

        elif action in ["pause", "resume", "next", "previous"]:
            state = "paused" if action == "pause" else "playing"
            current_song = user_service.get_current_playback(user_id)
            if current_song:
                current_song["state"] = state
                current_song["updated_at"] = datetime.now(timezone.utc)
                user_service.update_current_playback(user_id, current_song)
            else:
                current_song = {
                    "video_id": "",
                    "title": "",
                    "thumbnail_url": "",
                    "duration": 0,
                    "position": 0,
                    "state": state,
                    "mode": "default",
                    "motion_detected": user_doc.get("preferences", {}).get("motion_detection", True),
                    "updated_at": datetime.now(timezone.utc)
                }
                user_service.update_current_playback(user_id, current_song)

            command = {"action": action}
            success = pubnub_client.publish_message(user_doc['channel_name_commands'], command)
            if success:
                logger.info(f"Action '{action}' sent for user {user_id}.")
                return jsonify({"message": f"{action.capitalize()} command sent."}), 200
            else:
                return jsonify({"error": f"Failed to send {action} command."}), 500

        elif action == "seek":
            position = validated_data.get("position")
            if position is None:
                return jsonify({"error": "position is required for seek action."}), 400

            current_song = user_service.get_current_playback(user_id)
            if current_song:
                current_song["position"] = position
                current_song["updated_at"] = datetime.now(timezone.utc)
                user_service.update_current_playback(user_id, current_song)
            else:
                current_song = {
                    "video_id": "",
                    "title": "",
                    "thumbnail_url": "",
                    "duration": 0,
                    "position": position,
                    "state": "playing",
                    "mode": "default",
                    "motion_detected": user_doc.get("preferences", {}).get("motion_detection", True),
                    "updated_at": datetime.now(timezone.utc)
                }
                user_service.update_current_playback(user_id, current_song)

            command = {"action": "seek", "position": position}
            success = pubnub_client.publish_message(user_doc['channel_name_commands'], command)
            if success:
                logger.info(f"Seek command sent to position {position} for user {user_id}.")
                return jsonify({"message": "Seek command sent."}), 200
            else:
                return jsonify({"error": "Failed to send seek command."}), 500

        elif action == "set_mode":
            mode = validated_data.get("mode")
            if not mode:
                return jsonify({"error": "mode is required for set_mode action."}), 400

            current_song = user_service.get_current_playback(user_id)
            if current_song:
                current_song["mode"] = mode
                current_song["updated_at"] = datetime.now(timezone.utc)
                user_service.update_current_playback(user_id, current_song)
            else:
                current_song = {
                    "video_id": "",
                    "title": "",
                    "thumbnail_url": "",
                    "duration": 0,
                    "position": 0,
                    "state": "playing",
                    "mode": mode,
                    "motion_detected": user_doc.get("preferences", {}).get("motion_detection", True),
                    "updated_at": datetime.now(timezone.utc)
                }
                user_service.update_current_playback(user_id, current_song)

            command = {"action": "set_mode", "mode": mode}
            success = pubnub_client.publish_message(user_doc['channel_name_commands'], command)
            if success:
                logger.info(f"Set mode to '{mode}' for user {user_id}.")
                return jsonify({"message": "Set mode command sent."}), 200
            else:
                return jsonify({"error": "Failed to send set_mode command."}), 500

        elif action == "set_motion_detection":
            enabled = validated_data.get("enabled")
            if enabled is None:
                return jsonify({"error": "enabled is required for set_motion_detection action."}), 400

            preferences = user_doc.get("preferences", {})
            preferences["motion_detection"] = enabled
            user_service.save_preferences(user_id, preferences)
            logger.info(f"Set motion_detection to {enabled} for user {user_id}.")

            current_song = user_service.get_current_playback(user_id)
            if current_song:
                current_song["motion_detected"] = enabled
                current_song["updated_at"] = datetime.now(timezone.utc)
                user_service.update_current_playback(user_id, current_song)
            else:
                current_song = {
                    "video_id": "",
                    "title": "",
                    "thumbnail_url": "",
                    "duration": 0,
                    "position": 0,
                    "state": "playing",
                    "mode": "default",
                    "motion_detected": enabled,
                    "updated_at": datetime.now(timezone.utc)
                }
                user_service.update_current_playback(user_id, current_song)

            command = {"action": "set_motion_detection", "enabled": enabled}
            success = pubnub_client.publish_message(user_doc['channel_name_commands'], command)
            if success:
                logger.info(f"Set motion_detection to {enabled} command sent for user {user_id}.")
                return jsonify({"message": "Set motion_detection command sent."}), 200
            else:
                return jsonify({"error": "Failed to send set_motion_detection command."}), 500

    except Exception as e:
        logger.error(f"Error in handle_playback: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500
