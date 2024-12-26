# blueprints/auth.py
from flask import Blueprint, redirect, session, request, current_app
from services.authentication_service import AuthenticationService
from services.user_service import UserService
import os
from datetime import datetime, timezone
import traceback
import logging

auth_bp = Blueprint('auth', __name__)
auth_service = AuthenticationService(os.path.join(os.path.dirname(__file__), "../google_auth_secrets.json"))
logger = logging.getLogger(__name__)

@auth_bp.route("/login")
def login():
    flow = auth_service.create_flow("http://localhost:5000/login/authorized")
    authorization_url, state = flow.authorization_url(prompt="consent")
    session["state"] = state
    logger.info("Redirecting to Google authorization URL.")
    return redirect(authorization_url)

@auth_bp.route("/login/authorized")
def authorized():
    try:
        if "state" not in session or "state" not in request.args:
            logger.warning("Missing state in session or request arguments.")
            return redirect("/unauthorized")

        if session["state"] != request.args["state"]:
            logger.warning("State mismatch.")
            return redirect("/unauthorized")

        flow = auth_service.create_flow("http://localhost:5000/login/authorized")
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        client_id = flow.client_config.get('client_id')
        if not client_id:
            raise ValueError("client_id not found in client_config.")

        id_info = auth_service.verify_token(credentials.id_token, client_id)

        session["google_id"] = id_info.get("sub")
        session["name"] = id_info.get("name")
        session["email"] = id_info.get("email")

        google_id = session["google_id"]
        user_service: UserService = current_app.user_service
        user_doc = user_service.get_user_by_google_id(google_id)

        pubnub_client = current_app.pubnub_client

        if not user_doc:
            channel_name_commands = f"user_{google_id}_commands"
            channel_name_status = f"user_{google_id}_status"
            token_commands, expiration_commands = pubnub_client.generate_token([channel_name_commands], ttl=60)
            token_status, expiration_status = pubnub_client.generate_token([channel_name_status], ttl=60)

            if not token_commands or not token_status:
                logger.error("Failed to generate PubNub tokens.")
                return redirect("/unauthorized")

            user_doc = {
                "google_id": google_id,
                "name": session["name"],
                "email": session["email"],
                "channel_name_commands": channel_name_commands,
                "channel_name_status": channel_name_status,
                "channel_token_commands": token_commands,
                "channel_token_commands_expiration": expiration_commands,
                "channel_token_status": token_status,
                "channel_token_status_expiration": expiration_status,
                "playlists": [],
                "favorites": None,  # Ставимо None, створимо при необхідності
                "preferences": {
                    "volume": 0.5,
                    "led_mode": "default",
                    "motion_detection": True
                },
                "created_at": datetime.now(timezone.utc),
            }
            user_service.save_user(user_doc)
            logger.info(f"New user {google_id} saved.")

            # Створення документу favorites для користувача
            favorites_id = user_service.create_favorites(str(user_doc["_id"]))
            # Можливо, додати favorites_id до користувача
            user_service.update_user_tokens(google_id, {"favorites": favorites_id})
            logger.info(f"Favorites created for user {google_id} with ID {favorites_id}.")

        else:
            # Перевірка та оновлення токенів, якщо вони закінчилися
            tokens_updated = user_service.update_tokens_if_expired(google_id, user_doc)
            if tokens_updated:
                logger.info(f"Tokens updated for user {google_id}.")

        logger.info(f"User {google_id} authenticated successfully.")
        return redirect("/")
    except Exception as e:
        logger.error(f"Error during Google Login: {e}")
        logger.error(traceback.format_exc())
        return redirect("/unauthorized")
