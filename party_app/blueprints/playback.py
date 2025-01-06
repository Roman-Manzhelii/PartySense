from flask import Blueprint, jsonify, request, current_app
from services.user_service import UserService
from decorators.token_required import token_required
from marshmallow import Schema, fields, ValidationError
import logging
import traceback
from datetime import datetime, timezone

from youtube_api import get_video_details

logger = logging.getLogger(__name__)

class PlayCommandSchema(Schema):
    action = fields.String(
        required=True,
        validate=lambda x: x in [
            "play", "pause", "next", "previous",
            "seek", "set_mode", "set_motion_detection", "update_position"
        ]
    )
    video_id = fields.String(required=False)
    title = fields.String(required=False)
    thumbnail_url = fields.String(required=False)
    duration = fields.Integer(required=False)
    position = fields.Float(required=False)
    timestamp = fields.Integer(required=False)
    mode = fields.String(required=False, validate=lambda x: x in ["repeat", "default", "shuffle"])
    enabled = fields.Boolean(required=False)

play_command_schema = PlayCommandSchema()
playback_bp = Blueprint('playback', __name__)

@playback_bp.route("/api/playback", methods=["POST"])
@token_required
def handle_playback(current_user):
    try:
        data = request.get_json()
        validated_data = play_command_schema.load(data)
        action = validated_data.get("action")

        user_service: UserService = current_app.user_service
        pubnub_client = current_app.pubnub_client
        google_id = current_user["google_id"]

        video_id = validated_data.get("video_id")
        fallback_title = validated_data.get("title", "Unknown Title")
        fallback_thumb = validated_data.get("thumbnail_url", "")
        fallback_duration = validated_data.get("duration", 0)
        position = validated_data.get("position", 0.0)
        timestamp = validated_data.get("timestamp", 0)
        mode = validated_data.get("mode", "default")

        if action == "play":
            if not video_id:
                return jsonify({"error": "video_id is required for play action"}), 400

            details = get_video_details(video_id)
            if details:
                actual_title = details["title"] or fallback_title
                actual_thumb = details["thumbnail_url"] or fallback_thumb
                actual_duration = details["duration_seconds"] or fallback_duration
            else:
                actual_title = fallback_title
                actual_thumb = fallback_thumb
                actual_duration = fallback_duration

            current_song = {
                "video_id": video_id,
                "title": actual_title,
                "thumbnail_url": actual_thumb,
                "duration": actual_duration,
                "position": position,
                "state": "playing",
                "mode": mode,
                "motion_detected": current_user.get("preferences", {}).get("motion_detection", True),
                "updated_at": datetime.now(timezone.utc)
            }
            user_service.update_current_playback(google_id, current_song)
            user_service.log_playback_history(google_id, video_id, actual_title)

            command = {
                "action": "play",
                "video_id": video_id,
                "title": actual_title,
                "thumbnail_url": actual_thumb,
                "duration": actual_duration,
                "position": position,
                "timestamp": timestamp,
                "mode": mode
            }
            pubnub_client.publish_message(current_user["channel_name_commands"], command)
            logger.info(f"Published play command: {command}")
            return jsonify({"message": "Play command sent."}), 200

        elif action == "pause":
            logger.info(f"[handle_playback] 'pause' action received. position={position}, user={google_id}")
            curr = user_service.get_current_playback(google_id)
            if curr and "current_song" in curr:
                song = curr["current_song"]
                song["state"] = "pause"
                song["position"] = position
                song["updated_at"] = datetime.now(timezone.utc)
                user_service.update_current_playback(google_id, song)

            pubnub_client.publish_message(current_user["channel_name_commands"], {
                "action": "pause",
                "position": position,
                "timestamp": timestamp
            })
            return jsonify({"message": "Pause command sent."}), 200

        elif action in ["next", "previous"]:
            logger.info(f"[handle_playback] '{action}' action for user={google_id}")
            pubnub_client.publish_message(current_user["channel_name_commands"], {
                "action": action
            })
            return jsonify({"message": f"{action.capitalize()} command sent."}), 200

        elif action == "seek":
            logger.info(f"[handle_playback] 'seek' action. position={position}, user={google_id}")
            curr = user_service.get_current_playback(google_id)
            if curr and "current_song" in curr:
                song = curr["current_song"]
                song["position"] = position
                song["updated_at"] = datetime.now(timezone.utc)
                user_service.update_current_playback(google_id, song)

            pubnub_client.publish_message(current_user["channel_name_commands"], {
                "action": "seek",
                "position": position,
                "timestamp": timestamp
            })
            return jsonify({"message": "Seek command sent."}), 200

        elif action == "set_mode":
            logger.info(f"[handle_playback] 'set_mode'={mode}, user={google_id}")
            curr = user_service.get_current_playback(google_id)
            if curr and "current_song" in curr:
                song = curr["current_song"]
                song["mode"] = mode
                song["updated_at"] = datetime.now(timezone.utc)
                user_service.update_current_playback(google_id, song)

            pubnub_client.publish_message(current_user["channel_name_commands"], {
                "action": "set_mode",
                "mode": mode
            })
            return jsonify({"message": f"Set mode to {mode}."}), 200

        elif action == "set_motion_detection":
            enabled = validated_data.get("enabled", True)
            logger.info(f"[handle_playback] set_motion_detection={enabled}, user={google_id}")
            prefs = current_user.get("preferences", {})
            prefs["motion_detection"] = enabled
            user_service.save_preferences(google_id, prefs)

            curr = user_service.get_current_playback(google_id)
            if curr and "current_song" in curr:
                song = curr["current_song"]
                song["motion_detected"] = enabled
                song["updated_at"] = datetime.now(timezone.utc)
                user_service.update_current_playback(google_id, song)

            pubnub_client.publish_message(current_user["channel_name_commands"], {
                "action": "set_motion_detection",
                "enabled": enabled
            })
            return jsonify({"message": f"Motion detection => {enabled}"}), 200

        elif action == "update_position":
            logger.info(f"[handle_playback] 'update_position' for user={google_id}, position={position}")
            curr = user_service.get_current_playback(google_id)
            if not curr or "current_song" not in curr:
                logger.warning(f"No current_song found in DB for user={google_id}")
                return jsonify({"error": "No current song found"}), 400

            song = curr["current_song"]
            song["position"] = position
            song["updated_at"] = datetime.now(timezone.utc)

            if "state" not in song:
                song["state"] = "playing"

            user_service.update_current_playback(google_id, song)

            logger.info(f"[handle_playback] Updated position => {position} in DB for user={google_id}")
            return jsonify({"success": True, "message": "Position updated."}), 200

        else:
            return jsonify({"error": "Invalid action."}), 400

    except ValidationError as e:
        logger.error(f"ValidationError: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in handle_playback: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@playback_bp.route("/api/current_playback", methods=["GET"])
@token_required
def get_current_playback_route(current_user):
    try:
        google_id = current_user["google_id"]
        user_service: UserService = current_app.user_service
        current_playback = user_service.get_current_playback(google_id)
        if current_playback and "current_song" in current_playback:
            return jsonify({"current_song": current_playback["current_song"]}), 200
        else:
            return jsonify({"current_song": None}), 200
    except Exception as e:
        logger.error(f"Error in get_current_playback_route: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500
