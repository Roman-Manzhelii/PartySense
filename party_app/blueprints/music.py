from flask import Blueprint, jsonify, request, current_app
from services.music_service import MusicService
from decorators.token_required import token_required
import logging
import traceback

music_bp = Blueprint('music', __name__)
music_service = MusicService()
logger = logging.getLogger(__name__)

@music_bp.route("/control_music", methods=["POST"])
@token_required
def control_music_route(current_user):
    try:
        user_doc = current_user
        action = request.json.get("action")
        if not action or action not in ["pause", "resume", "next", "previous"]:
            logger.warning("Invalid action received in /control_music.")
            return jsonify({"error": "Invalid action"}), 400

        pubnub_client = current_app.pubnub_client

        # Публікація повідомлення до PubNub
        success = pubnub_client.publish_message(user_doc['channel_name_commands'], {'action': action})
        if success:
            logger.info(f"Music control action '{action}' published successfully.")
            return jsonify({"success": True}), 200
        else:
            logger.error("Failed to publish music control action.")
            return jsonify({"error": "Failed to publish action"}), 500

    except Exception as e:
        logger.error(f"Error in control_music_route: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500
