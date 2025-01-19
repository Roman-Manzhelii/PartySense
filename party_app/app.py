from flask import Flask, session, render_template, request, redirect
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone

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

last_playback_states = {}
last_update_times = {}

def handle_status_update(message):
    try:
        user_id = message.get("user_id")
        current_song = message.get("current_song")
        if not user_id or not current_song:
            logger.error("Invalid status message received.")
            return
        logger.info(f"[handle_status_update] got message: {message}")

        now = datetime.now(timezone.utc)
        last_state = last_playback_states.get(user_id)
        last_update = last_update_times.get(user_id, now - timedelta(seconds=10))

        existing_db = app.user_service.get_current_playback(user_id)
        if existing_db and "current_song" in existing_db:
            db_song = existing_db["current_song"]
            db_pos = db_song.get("position", 0)
            msg_pos = current_song.get("position", 0)
            if msg_pos < db_pos:
                logger.info(f"[handle_status_update] ignoring older position msg_pos={msg_pos} < db_pos={db_pos}")
                return

        if last_state != current_song:
            state_changed = False
            if last_state is None:
                state_changed = True
            else:
                for key in ["video_id", "title", "state", "position", "mode", "motion_detected"]:
                    if last_state.get(key) != current_song.get(key):
                        state_changed = True
                        break

            if state_changed and (now - last_update) >= timedelta(seconds=1):
                last_playback_states[user_id] = current_song
                last_update_times[user_id] = now

                app.user_service.update_current_playback(str(user_id), current_song)
                logger.info(f"Updated current_playback for user {user_id}.")

                socketio.emit('playback_update', {'user_id': user_id, 'current_song': current_song})
                logger.info(f"Emitted playback_update for user {user_id}.")
            else:
                logger.debug(f"Update for user {user_id} skipped due to frequency limit.")
        else:
            logger.debug(f"No significant change in playback state for user {user_id}. Skipping emission.")
    except Exception as e:
        logger.error(f"Error handling status update: {e}")

pubnub_client = PubNubClient(handle_status_update)
app.pubnub_client = pubnub_client

user_service = UserService(pubnub_client)
app.user_service = user_service

music_service = MusicService()
app.music_service = music_service

search_service = SearchService()

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
    return redirect("/")

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
        user_ids = [user["google_id"] for user in users]
        pubnub_client.subscribe_to_channels(user_ids)
        logger.info("Subscribed to all existing users' status channels.")

    socketio.run(app, host="0.0.0.0", port=5000)
