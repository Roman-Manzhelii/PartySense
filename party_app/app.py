from flask import Flask, jsonify, session, render_template, request, redirect
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pubnub_app.pubnub_client import PubNubClient
from youtube_api import search_youtube_music, play_youtube_music, control_music, fetch_video_title, autocomplete_music
from mongodb_client import (
    get_user_by_google_id,
    save_preferences,
    get_preferences,
    log_playback_history,
    save_user,
    update_user_token,
)

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_FLASK_KEY", "DEFAULT_SECRET_KEY")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Enable HTTP for testing
client_secrets_file = os.path.join(os.path.dirname(__file__), "google_auth_secrets.json")

# PubNub setup
pubnub_client = PubNubClient()

# Google OAuth 2.0 scopes
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

ALLOWED_LED_MODES = ["default", "party", "chill"]

@app.route("/", methods=["GET", "POST"])
def dashboard():
    if "google_id" not in session:
        return redirect("/login")

    google_id = session["google_id"]
    user_doc = get_user_by_google_id(google_id)

    if not user_doc:
        return redirect("/unauthorized")

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_preferences":
            volume = float(request.form.get("volume", 50)) / 100  # Convert from percentage
            led_mode = request.form.get("led_mode", "default")
            save_preferences(google_id, volume, led_mode)
            pubnub_client.publish_message(user_doc["channel_name"], {"volume": volume, "led_mode": led_mode})

        elif action == "play_music":
            video_id = request.form.get("video_id")
            if video_id:
                video_title = fetch_video_title(video_id) or "Unknown Title"
                play_youtube_music(video_id)
                log_playback_history(google_id, video_id, video_title)
                pubnub_client.publish_message(user_doc["channel_name"], {"action": "play", "video_id": video_id})

    preferences = get_preferences(google_id) or {"volume": 0.5, "led_mode": "default"}
    return render_template(
        "dashboard.html",
        user=session.get("name"),
        preferences=preferences,
        allowed_modes=ALLOWED_LED_MODES,
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/control_music", methods=["POST"])
def control_music_route():
    if "google_id" not in session:
        return redirect("/unauthorized")

    google_id = session["google_id"]
    user_doc = get_user_by_google_id(google_id)

    if not user_doc:
        return redirect("/unauthorized")

    action = request.json.get("action")
    if not action or action not in ["pause", "resume", "next", "previous"]:
        return jsonify({"error": "Invalid action"}), 400

    if control_music(action):
        pubnub_client.publish_message(user_doc["channel_name"], {"action": action})
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to control music"}), 500

@app.route("/search", methods=["GET"])
def search_music():
    if "google_id" not in session:
        return redirect("/unauthorized")

    query = request.args.get("query", "")
    page_token = request.args.get("pageToken", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    # Додаткове логування для відлагодження
    print(f"Search query: '{query}', Page token: '{page_token}'")

    try:
        results = search_youtube_music(query, page_token=page_token)
        if results:
            print(f"Next Page Token: {results.get('nextPageToken')}")
            return jsonify(results)
        else:
            return jsonify({"error": "Failed to fetch results"}), 500
    except Exception as e:
        print(f"Error during search: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    query = request.args.get("query", "")
    if not query:
        return jsonify([])

    suggestions = autocomplete_music(query)
    return jsonify(suggestions)

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
        user_doc = get_user_by_google_id(google_id)

        if not user_doc:
            channel_name = f"settings_channel_{google_id}"
            token = pubnub_client.generate_token([channel_name])
            user_doc = {
                "google_id": google_id,
                "name": session["name"],
                "email": session["email"],
                "channel_name": channel_name,
                "channel_token": token,
                "created_at": datetime.now(timezone.utc),
            }
            save_user(user_doc)
        else:
            channel_name = user_doc["channel_name"]
            if pubnub_client.is_token_expired(user_doc["channel_token"]):
                new_token = pubnub_client.generate_token([channel_name])
                update_user_token(google_id, new_token)

        return redirect("/")
    except Exception as e:
        print(f"Error during Google Login: {e}")
        return redirect("/unauthorized")

@app.route("/unauthorized")
def unauthorized():
    return jsonify({"error": "Unauthorized access"}), 401

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
