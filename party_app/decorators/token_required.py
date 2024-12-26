# decorators/token_required.py
from functools import wraps
from flask import jsonify, session, redirect, current_app
from services.user_service import UserService
import logging
import traceback
from datetime import timezone

logger = logging.getLogger(__name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            if "google_id" not in session:
                logger.warning("Unauthorized access attempt.")
                return redirect("/unauthorized")

            google_id = session["google_id"]
            user_service: UserService = current_app.user_service
            user_doc = user_service.get_user_by_google_id(google_id)

            if not user_doc:
                logger.error(f"User with google_id {google_id} not found.")
                return redirect("/unauthorized")

            pubnub_client = current_app.pubnub_client

            # Перевірка та оновлення токенів для channel_commands
            token_commands = user_doc.get('channel_token_commands')
            expiration_commands = user_doc.get('channel_token_commands_expiration')

            if token_commands and expiration_commands:
                # Переконайтеся, що expiration_commands є timezone-aware
                if expiration_commands.tzinfo is None:
                    expiration_commands = expiration_commands.replace(tzinfo=timezone.utc)
                if pubnub_client.is_token_expired(expiration_commands):
                    new_token_commands, new_expiration_commands = pubnub_client.generate_token([user_doc['channel_name_commands']])
                    if new_token_commands:
                        user_service.update_user_tokens(google_id, {
                            "channel_token_commands": new_token_commands,
                            "channel_token_commands_expiration": new_expiration_commands
                        })
                        logger.info(f"Updated channel_token_commands for user {google_id}")
                    else:
                        logger.error("Failed to update channel_token_commands.")
                        return jsonify({'error': 'Failed to update token'}), 500

            # Перевірка та оновлення токенів для channel_status
            token_status = user_doc.get('channel_token_status')
            expiration_status = user_doc.get('channel_token_status_expiration')

            if token_status and expiration_status:
                # Переконайтеся, що expiration_status є timezone-aware
                if expiration_status.tzinfo is None:
                    expiration_status = expiration_status.replace(tzinfo=timezone.utc)
                if pubnub_client.is_token_expired(expiration_status):
                    new_token_status, new_expiration_status = pubnub_client.generate_token([user_doc['channel_name_status']])
                    if new_token_status:
                        user_service.update_user_tokens(google_id, {
                            "channel_token_status": new_token_status,
                            "channel_token_status_expiration": new_expiration_status
                        })
                        logger.info(f"Updated channel_token_status for user {google_id}")
                    else:
                        logger.error("Failed to update channel_token_status.")
                        return jsonify({'error': 'Failed to update token'}), 500

            # Передача current_user до декорованої функції
            return f(current_user=user_doc, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in token_required decorator: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Internal server error'}), 500

    return decorated