from flask import Flask, jsonify, redirect, session, render_template, request, flash
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pubnub_app.pubnub_client import PubNubClient
from youtube_api import search_youtube_music, get_user_playlists, play_youtube_music

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_FLASK_KEY", "DEFAULT_SECRET_KEY")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Enable HTTP for testing
client_secrets_file = os.path.join(os.path.dirname(__file__), "google_auth_secrets.json")

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/party_sense_db")
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["party_sense_db"]
users_collection = db["users"]

# PubNub setup
pubnub_client = PubNubClient()

# Google OAuth 2.0 scopes
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

ALLOWED_LED_MODES = ["default", "party", "chill"]

@app.route("/")
def index():
    if "google_id" not in session:
        return redirect("/login")
    return render_template("index.html", user=session.get("name"))

@app.route("/login")
def login():
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=SCOPES,
        redirect_uri="http://localhost:5000/login/authorized",
    )
    authorization_url, state = flow.authorization_url(prompt="consent")
    session["state"] = state
    return redirect(authorization_url)

@app.route("/login/authorized")
def authorized():
    try:
        if "state" not in session or "state" not in request.args:
            return redirect("/unauthorized")

        if session["state"] != request.args["state"]:
            return redirect("/unauthorized")

        flow = Flow.from_client_secrets_file(
            client_secrets_file=client_secrets_file,
            scopes=SCOPES,
            state=session["state"],
            redirect_uri="http://localhost:5000/login/authorized",
        )
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        request_session = google.auth.transport.requests.Request()
        id_info = id_token.verify_oauth2_token(
            id_token=credentials.id_token,
            request=request_session,
            audience=flow.client_config["client_id"],
        )

        session["google_id"] = id_info.get("sub")
        session["name"] = id_info.get("name")
        session["email"] = id_info.get("email")

        google_id = session["google_id"]
        user_doc = users_collection.find_one({"google_id": google_id})

        if not user_doc:
            channel_name = f"settings_channel_{google_id}"
            token = pubnub_client.generate_token([channel_name])
            users_collection.insert_one({
                "google_id": google_id,
                "name": session["name"],
                "email": session["email"],
                "preferences": {"volume": 0.5, "led_mode": "default"},
                "channel_name": channel_name,
                "channel_token": token,
            })
        else:
            channel_name = user_doc.get("channel_name")
            if not channel_name:
                channel_name = f"settings_channel_{google_id}"
                users_collection.update_one({"google_id": google_id}, {"$set": {"channel_name": channel_name}})
            if pubnub_client.is_token_expired(user_doc.get("channel_token")):
                new_token = pubnub_client.generate_token([channel_name])
                users_collection.update_one({"google_id": google_id}, {"$set": {"channel_token": new_token}})

        return redirect("/")
    except Exception as e:
        print(f"Error during Google Login: {e}")
        return redirect("/unauthorized")

@app.route("/search", methods=["GET"])
def search_music():
    if "google_id" not in session:
        return redirect("/unauthorized")

    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    results = search_youtube_music(query)
    return jsonify(results)

@app.route("/playlists", methods=["GET"])
def playlists():
    if "google_id" not in session:
        return redirect("/unauthorized")

    playlists = get_user_playlists()
    return jsonify(playlists)

@app.route("/play", methods=["POST"])
def play_music():
    if "google_id" not in session:
        return redirect("/unauthorized")

    video_id = request.json.get("video_id")
    if not video_id:
        return jsonify({"error": "No video ID provided"}), 400

    success = play_youtube_music(video_id)
    return jsonify({"success": success})

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "google_id" not in session:
        return redirect("/unauthorized")

    google_id = session["google_id"]
    user_doc = users_collection.find_one({"google_id": google_id})
    if not user_doc:
        return redirect("/unauthorized")

    current_prefs = user_doc.get("preferences", {})
    current_volume = current_prefs.get("volume", 0.5)
    current_led_mode = current_prefs.get("led_mode", "default")

    if request.method == "POST":
        volume = request.form.get("volume", "").strip()
        led_mode = request.form.get("led_mode", "").strip()

        error_msg = None
        try:
            volume_percent = int(volume)
            if volume_percent < 0 or volume_percent > 100:
                error_msg = "Volume must be between 0% and 100%."
            else:
                volume = volume_percent / 100.0
        except ValueError:
            error_msg = "Volume must be a number between 0 and 100."

        if led_mode not in ALLOWED_LED_MODES:
            error_msg = "Invalid LED mode selected."

        if error_msg:
            flash(error_msg, "error")
        else:
            users_collection.update_one(
                {"google_id": google_id},
                {"$set": {
                    "preferences.volume": volume,
                    "preferences.led_mode": led_mode,
                }}
            )
            channel_name = user_doc.get("channel_name")
            pubnub_client.publish_message(channel_name, {"volume": volume, "led_mode": led_mode})

            flash("Settings updated successfully!", "success")
            current_volume = volume
            current_led_mode = led_mode

    return render_template("settings.html", volume=current_volume, led_mode=current_led_mode, allowed_modes=ALLOWED_LED_MODES)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/unauthorized")
def unauthorized():
    return jsonify({"error": "Unauthorized access"}), 401

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
