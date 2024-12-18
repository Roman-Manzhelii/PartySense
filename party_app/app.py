import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
from flask import Flask, jsonify, redirect, session, url_for, abort, render_template, request
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_FLASK_KEY")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
client_secrets_file = os.path.join(os.path.dirname(__file__), "google_auth_secrets.json")

SCOPES = ["https://www.googleapis.com/auth/userinfo.profile", 
          "https://www.googleapis.com/auth/userinfo.email", 
          "openid"]

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

        # Використовуємо звичайну сесію requests без cachecontrol
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
    # Запускаємо додаток локально за адресою http://localhost:5000
    app.run(host="localhost", port=5000, debug=True)
