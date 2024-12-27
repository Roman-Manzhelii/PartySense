from flask import Flask, session, render_template, request, redirect
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv
import logging

load_dotenv()

from services.user_service import UserService
from services.music_service import MusicService
from services.search_service import SearchService
from pubnub_app.pubnub_client import PubNubClient
from decorators.token_required import token_required

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_FLASK_KEY", "DEFAULT_SECRET_KEY")
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

socketio = SocketIO(app)

# PubNub
pubnub_client = PubNubClient()
app.pubnub_client = pubnub_client

# Сервіси
music_service = MusicService()
app.music_service = music_service

search_service = SearchService()

user_service = UserService(pubnub_client)
app.user_service = user_service

# Імпортуємо Blueprint'и
from blueprints.auth import auth_bp
from blueprints.music import music_bp
from blueprints.search import search_bp
from blueprints.playlists import playlists_bp
from blueprints.favorites import favorites_bp
from blueprints.categories import categories_bp
from blueprints.playback import playback_bp
from blueprints.preferences import preferences_bp

app.register_blueprint(auth_bp)
app.register_blueprint(music_bp)
app.register_blueprint(search_bp)
app.register_blueprint(playlists_bp)
app.register_blueprint(favorites_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(playback_bp)
app.register_blueprint(preferences_bp)

def handle_status_update(message):
    try:
        user_id = message.get("user_id")
        current_song = message.get("current_song")
        if not user_id or not current_song:
            logger.error("Invalid status message received.")
            return

        app.user_service.update_current_playback(str(user_id), current_song)
        logger.info(f"Updated current_playback for user {user_id}.")

        socketio.emit('playback_update', {'user_id': user_id, 'current_song': current_song}, broadcast=True)
        logger.info(f"Emitted playback_update for user {user_id}.")
    except Exception as e:
        logger.error(f"Error handling status update: {e}")

@app.route("/", methods=["GET", "POST"])
@token_required
def dashboard(current_user):
    google_id = current_user["google_id"]
    user_doc = user_service.get_user_by_google_id(google_id)
    if not user_doc:
        return redirect("/unauthorized")

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_preferences":
            volume = min(max(float(request.form.get("volume", 50)) / 100, 0), 1)
            led_mode = request.form.get("led_mode", "default")
            motion_detection = 'motion_detection' in request.form
            prefs = {
                "volume": volume,
                "led_mode": led_mode,
                "motion_detection": motion_detection
            }
            user_service.save_preferences(google_id, prefs)
            pubnub_client.publish_message(user_doc["channel_name_commands"], {
                "action": "update_preferences",
                "preferences": prefs
            })

    preferences = user_service.get_preferences(google_id) or {
        "volume": 0.5, "led_mode": "default", "motion_detection": True
    }
    favorites_doc = user_service.get_favorites(google_id)
    favorites_list = favorites_doc.get("songs", []) if favorites_doc else []

    return render_template(
        "dashboard.html",
        user=current_user.get("name"),
        preferences=preferences,
        allowed_modes=["default", "party", "chill"],
        favorites=favorites_list
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/unauthorized")
def unauthorized():
    return render_template('unauthorized.html'), 401

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected via WebSocket.")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected from WebSocket.")

if __name__ == "__main__":
    from mongodb_client import create_indexes
    create_indexes()

    with app.app_context():
        users = app.user_service.get_all_users()
        for user in users:
            gid = user["google_id"]
            pubnub_client.subscribe_to_status_channel(gid, handle_status_update)
        logger.info("Subscribed to all existing users' status channels.")

    socketio.run(app, host="localhost", port=5000, debug=True)
