from flask import Blueprint, jsonify, request, current_app
from services.user_service import UserService
from decorators.token_required import token_required
from marshmallow import Schema, fields, ValidationError
import logging
import traceback
from datetime import datetime, timezone

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
    title = fields.String(required=False)
    thumbnail_url = fields.String(required=False)
    duration = fields.Integer(required=False)
    position = fields.Float(required=False)    # Поточний момент треку
    timestamp = fields.Integer(required=False) # Час на боці клієнта (мс)
    mode = fields.String(required=False, validate=lambda x: x in ["repeat", "default", "shuffle"])
    enabled = fields.Boolean(required=False)   # Для set_motion_detection

play_command_schema = PlayCommandSchema()
playback_bp = Blueprint('playback', __name__)

@playback_bp.route("/api/playback", methods=["POST"])
@token_required
def handle_playback(current_user):
    try:
        data = request.get_json()
        # Валідую вхідні дані через Marshmallow
        validated_data = play_command_schema.load(data)
        action = validated_data.get("action")

        # Поточний користувач
        user_id = str(current_user["_id"])
        google_id = current_user["google_id"]

        # Сервіси
        user_service: UserService = current_app.user_service
        pubnub_client = current_app.pubnub_client

        # Збираємо параметри, що можуть прийти
        video_id = validated_data.get("video_id")
        title = validated_data.get("title", "Unknown Title")
        thumbnail_url = validated_data.get("thumbnail_url", "")
        duration = validated_data.get("duration", 0)
        position = validated_data.get("position", 0.0)
        timestamp = validated_data.get("timestamp", 0)
        mode = validated_data.get("mode", "default")

        if action == "play":
            # Перевірка
            if not video_id:
                return jsonify({"error": "video_id is required for play action"}), 400

            # Формуємо current_song для Mongo
            current_song = {
                "video_id": video_id,
                "title": title,
                "thumbnail_url": thumbnail_url,
                "duration": duration,
                "position": position,
                "state": "playing",
                "mode": mode,
                "motion_detected": current_user.get("preferences", {}).get("motion_detection", True),
                "updated_at": datetime.now(timezone.utc)
            }
            # Оновлюємо current_playback
            user_service.update_current_playback(google_id, current_song)

            # Логування історії відтворення
            user_service.log_playback_history(google_id, video_id, title)

            # Формуємо повідомлення PubNub
            command = {
                "action": "play",
                "video_id": video_id,
                "title": title,
                "thumbnail_url": thumbnail_url,
                "duration": duration,
                "position": position,
                "timestamp": timestamp,
                "mode": mode
            }
            pubnub_client.publish_message(current_user["channel_name_commands"], command)

            return jsonify({"message": "Play command sent."}), 200

        elif action == "pause":
            # Оновити state="paused", зберегти position
            curr = user_service.get_current_playback(google_id)
            if curr and "current_song" in curr:
                song = curr["current_song"]
                song["state"] = "paused"
                song["position"] = position
                song["updated_at"] = datetime.now(timezone.utc)
                user_service.update_current_playback(google_id, song)

            # Надсилаємо в PubNub
            pubnub_client.publish_message(current_user["channel_name_commands"], {
                "action": "pause",
                "position": position,
                "timestamp": timestamp
            })
            return jsonify({"message": "Pause command sent."}), 200

        elif action == "resume":
            curr = user_service.get_current_playback(google_id)
            if curr and "current_song" in curr:
                song = curr["current_song"]
                song["state"] = "playing"
                song["position"] = position
                song["updated_at"] = datetime.now(timezone.utc)
                user_service.update_current_playback(google_id, song)

            pubnub_client.publish_message(current_user["channel_name_commands"], {
                "action": "resume",
                "position": position,
                "timestamp": timestamp
            })
            return jsonify({"message": "Resume command sent."}), 200

        elif action in ["next", "previous"]:
            # Просто шлемо команду на Pi, Mongo не змінюємо
            pubnub_client.publish_message(current_user["channel_name_commands"], {
                "action": action
            })
            return jsonify({"message": f"{action.capitalize()} command sent."}), 200

        elif action == "seek":
            # Оновлюємо позицію
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
            # repeat / shuffle / default
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
            # Припустимо, що enabled у схемі
            enabled = validated_data.get("enabled", True)

            # Оновлюємо preferences
            prefs = current_user.get("preferences", {})
            prefs["motion_detection"] = enabled
            user_service.save_preferences(google_id, prefs)

            # Оновлюємо current_playback (якщо треба)
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

        return jsonify({"error": "Invalid action."}), 400

    except ValidationError as e:
        logger.error(f"ValidationError: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in handle_playback: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500
