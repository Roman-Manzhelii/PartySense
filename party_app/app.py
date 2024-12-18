import os
import pathlib
from flask import Flask, jsonify, redirect, session, url_for, abort, render_template, request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_FLASK_KEY")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
client_secrets_file = os.path.join(os.path.dirname(__file__), "google_auth_secrets.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://localhost:5000/login/authorized"
)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    if "google_id" not in session:
        return redirect("/login")
    return render_template("index.html", user=session.get("name"))

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/login/authorized")
def authorized():
    try:
        flow.fetch_token(authorization_response=request.url)
        if session["state"] != request.args["state"]:
            abort(500)

        credentials = flow.credentials
        request_session = cachecontrol.CacheControl(google.auth.transport.requests.Request())

        # Додайте перевірку
        print(f"Fetched token: {credentials._id_token}")
        
        id_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=request_session,
            audience=GOOGLE_CLIENT_ID
        )

        print("ID Token Info:", id_info)

        session["google_id"] = id_info.get("sub")
        session["name"] = id_info.get("name")
        session["email"] = id_info.get("email")
        return redirect("/")
    except Exception as e:
        print(f"Error during Google Login: {e}")
        return redirect("/unauthorized")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/unauthorized")
def unauthorized():
    return jsonify({"error": "Unauthorized access"}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
