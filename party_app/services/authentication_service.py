from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests

class AuthenticationService:
    def __init__(self, client_secrets_file):
        self.client_secrets_file = client_secrets_file
        self.scopes = [
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
        ]

    def create_flow(self, redirect_uri):
        flow = Flow.from_client_secrets_file(
            self.client_secrets_file,
            scopes=self.scopes,
            redirect_uri=redirect_uri,
        )
        return flow

    def verify_token(self, token, audience):
        try:
            request_session = google.auth.transport.requests.Request()
            id_info = id_token.verify_oauth2_token(
                id_token=token,
                request=request_session,
                audience=audience,
                clock_skew_in_seconds=10
            )
            return id_info
        except Exception as e:
            raise e
