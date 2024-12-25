# app.py
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

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_FLASK_KEY", "DEFAULT_SECRET_KEY")

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

# Регістрація Blueprint'ів
from blueprints.auth import auth_bp
from blueprints.music import music_bp
from blueprints.search import search_bp

app.register_blueprint(auth_bp)
app.register_blueprint(music_bp)
app.register_blueprint(search_bp)

# Маршрут Dashboard
@app.route("/", methods=["GET", "POST"])
def dashboard():
    if "google_id" not in session:
        return redirect("/login")

    google_id = session["google_id"]
    user_doc = user_service.get_user_by_google_id(google_id)

    if not user_doc:
        return redirect("/unauthorized")

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_preferences":
            volume = float(request.form.get("volume", 50)) / 100  # Конвертація з процентів
            led_mode = request.form.get("led_mode", "default")
            # Припускаємо, що motion_detection - це чекбокс
            motion_detection = request.form.get("motion_detection", "on") == "on"
            preferences = {
                "volume": volume,
                "led_mode": led_mode,
                "motion_detection": motion_detection
            }
            user_service.save_preferences(google_id, preferences)
            # Публікація оновлення налаштувань
            pubnub_client.publish_message(user_doc["channel_name_commands"], {
                "action": "update_preferences",
                "preferences": preferences
            })
            logger.info(f"Preferences updated for user {google_id}.")

        elif action == "play_music":
            video_id = request.form.get("video_id")
            if video_id:
                video_title = music_service.fetch_video_title(video_id) or "Unknown Title"
                music_service.play_youtube_music(video_id)
                user_service.log_playback_history(google_id, video_id, video_title)
                # Публікація команди Play
                pubnub_client.publish_message(user_doc["channel_name_commands"], {
                    "action": "play",
                    "video_id": video_id,
                    "position": 0  # Початок
                })
                logger.info(f"Play command sent for video_id {video_id}.")

    preferences = user_service.get_preferences(google_id) or {
        "volume": 0.5, "led_mode": "default", "motion_detection": True
    }
    return render_template(
        "dashboard.html",
        user=session.get("name"),
        preferences=preferences,
        allowed_modes=["default", "party", "chill"],  # Приклад дозволених режимів
    )

# Маршрут Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Маршрут Unauthorized
@app.route("/unauthorized")
def unauthorized():
    return render_template('unauthorized.html'), 401

if __name__ == "__main__":
    from mongodb_client import create_indexes
    create_indexes()
    
    socketio.run(app, host="localhost", port=5000, debug=True)
