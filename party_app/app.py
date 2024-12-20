import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
from flask import Flask, jsonify, redirect, session, url_for, abort, render_template, request
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_FLASK_KEY")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
client_secrets_file = os.path.join(os.path.dirname(__file__), "google_auth_secrets.json")

MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["party_sense_db"]
users_collection = db["users"]

SCOPES = ["https://www.googleapis.com/auth/userinfo.profile", 
          "https://www.googleapis.com/auth/userinfo.email", 
          "openid"]

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
        redirect_uri="http://localhost:5000/login/authorized"
    )
    authorization_url, state = flow.authorization_url(prompt='consent')
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
            redirect_uri="http://localhost:5000/login/authorized"
        )

        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        session_requests = requests.Session()
        request_session = google.auth.transport.requests.Request(session=session_requests)

        id_info = id_token.verify_oauth2_token(
            id_token=credentials.id_token,
            request=request_session,
            audience=flow.client_config['client_id']
        )

        session["google_id"] = id_info.get("sub")
        session["name"] = id_info.get("name")
        session["email"] = id_info.get("email")

        # Check if user exists in DB, else create with default preferences
        user_doc = users_collection.find_one({"google_id": session["google_id"]})
        if not user_doc:
            users_collection.insert_one({
                "google_id": session["google_id"],
                "name": session["name"],
                "email": session["email"],
                "preferences": {
                    "volume": 0.5,
                    "led_mode": "default"
                }
            })

        return redirect("/")
    except Exception as e:
        print(f"Error during Google Login: {e}")
        return redirect("/unauthorized")

@app.route("/user_prefs")
def user_prefs():
    if "google_id" not in session:
        return redirect("/unauthorized")
    user_doc = users_collection.find_one({"google_id": session["google_id"]}, {"_id": 0})
    if not user_doc:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user_doc.get("preferences", {}))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/unauthorized")
def unauthorized():
    return jsonify({"error": "Unauthorized access"}), 401

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)