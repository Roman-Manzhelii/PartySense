from flask import Flask, session, render_template, request, redirect
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv
import logging

# Завантаження змінних середовища
load_dotenv()

from services.user_service import UserService
from services.music_service import MusicService
from services.search_service import SearchService
from pubnub_app.pubnub_client import PubNubClient
from decorators.token_required import token_required

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація Flask
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_FLASK_KEY", "DEFAULT_SECRET_KEY")

# Налаштування Cookie
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Ініціалізація SocketIO
socketio = SocketIO(app)

# Ініціалізація PubNubClient
pubnub_client = PubNubClient()
app.pubnub_client = pubnub_client  # Додаємо до додатку

# Ініціалізація UserService з PubNubClient
user_service = UserService(pubnub_client)
app.user_service = user_service  # Додаємо до додатку

# Ініціалізація інших сервісів
music_service = MusicService()
search_service = SearchService()

# Імпортуємо та реєструємо Blueprint'и
from blueprints.auth import auth_bp
from blueprints.music import music_bp
from blueprints.search import search_bp
from blueprints.playlists import playlists_bp
from blueprints.favorites import favorites_bp
from blueprints.categories import categories_bp
from blueprints.playback import playback_bp

app.register_blueprint(auth_bp)
app.register_blueprint(music_bp)
app.register_blueprint(search_bp)
app.register_blueprint(playlists_bp)
app.register_blueprint(favorites_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(playback_bp)


def handle_status_update(message):
    try:
        user_id = message.get("user_id")
        current_song = message.get("current_song")

        if not user_id or not current_song:
            logger.error("Invalid status message received.")
            return

        app.user_service.update_current_playback(str(user_id), current_song)
        logger.info(f"Updated current_playback for user {user_id}.")

        # Відправка оновлення через WebSocket
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
            # Обробка зміни налаштувань
            volume = min(max(float(request.form.get("volume", 50)) / 100, 0), 1)
            led_mode = request.form.get("led_mode", "default")
            motion_detection = 'motion_detection' in request.form
            preferences = {
                "volume": volume,
                "led_mode": led_mode,
                "motion_detection": motion_detection
            }
            user_service.save_preferences(google_id, preferences)
            logger.info(f"Preferences updated for user {google_id}.")

            pubnub_client.publish_message(user_doc["channel_name_commands"], {
                "action": "update_preferences",
                "preferences": preferences
            })

        elif action == "play_music":
            video_id = request.form.get("video_id")
            if video_id:
                video_title = music_service.fetch_video_title(video_id) or "Unknown Title"
                music_service.play_youtube_music(video_id)
                user_service.log_playback_history(google_id, video_id, video_title)
                logger.info(f"Play command sent for video_id {video_id}.")

                pubnub_client.publish_message(user_doc["channel_name_commands"], {
                    "action": "play",
                    "video_id": video_id,
                    "position": 0
                })

    # Завантаження налаштувань
    preferences = user_service.get_preferences(google_id) or {
        "volume": 0.5, "led_mode": "default", "motion_detection": True
    }

    # Завантаження улюблених треків
    favorites = user_service.get_favorites(google_id)
    favorites_list = favorites.get("songs", []) if favorites else []

    return render_template(
        "dashboard.html",
        user=current_user.get("name"),
        preferences=preferences,
        allowed_modes=["default", "party", "chill"],  # Приклад дозволених режимів
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

    # Перед запуском сервера підписуємося на статус-канали
    with app.app_context():
        users = app.user_service.get_all_users()
        for user in users:
            # Використовуємо google_id замість _id
            google_id = user["google_id"]
            pubnub_client.subscribe_to_status_channel(google_id, handle_status_update)
        logger.info("Subscribed to all existing users' status channels.")

    socketio.run(app, host="localhost", port=5000, debug=True)
