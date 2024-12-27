# файл: blueprints/preferences.py

from flask import Blueprint, request, jsonify, current_app
from decorators.token_required import token_required
import logging
import traceback

logger = logging.getLogger(__name__)

preferences_bp = Blueprint("preferences", __name__)

@preferences_bp.route("/api/preferences", methods=["POST"])
@token_required
def update_preferences(current_user):
    try:
        data = request.get_json() or {}

        google_id = current_user["google_id"]
        user_service = current_app.user_service
        pubnub_client = current_app.pubnub_client

        # Тягнемо поточні налаштування з бази
        existing_prefs = user_service.get_preferences(google_id) or {}

        # Оновлюємо лише ті поля, що прийшли з клієнта
        if "volume" in data:
            existing_prefs["volume"] = data["volume"]
        if "led_mode" in data:
            existing_prefs["led_mode"] = data["led_mode"]
        if "motion_detection" in data:
            existing_prefs["motion_detection"] = data["motion_detection"]

        # Зберігаємо у Mongo
        user_service.save_preferences(google_id, existing_prefs)

        # Надсилаємо повідомлення на канал команд
        pubnub_client.publish_message(
            current_user["channel_name_commands"],
            {
                "action": "update_preferences",
                "preferences": existing_prefs
            }
        )
        logger.info(f"Preferences updated for user {google_id} and published to PubNub.")

        return jsonify({
            "message": "Preferences updated successfully.",
            "preferences": existing_prefs
        }), 200

    except Exception as e:
        logger.error(f"Error in update_preferences: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
