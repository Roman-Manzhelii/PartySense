# services/user_service.py
from mongodb_client import (
    get_user_by_google_id,
    save_user,
    save_preferences,
    get_preferences,
    log_playback_history,
    update_user_token,
    get_all_users
)

class UserService:
    def __init__(self, pubnub_client):
        self.pubnub_client = pubnub_client

    def get_user_by_google_id(self, google_id):
        return get_user_by_google_id(google_id)
    
    def save_user(self, user_doc):
        save_user(user_doc)

    def save_preferences(self, google_id, preferences):
        save_preferences(google_id, preferences)

    def get_preferences(self, google_id):
        return get_preferences(google_id)

    def log_playback_history(self, google_id, video_id, title):
        log_playback_history(google_id, video_id, title)

    def update_user_tokens(self, google_id, new_tokens):
        update_user_token(google_id, new_tokens)

    def update_tokens_if_expired(self, google_id, user_doc):
        tokens_updated = False

        # Перевірка та оновлення токенів для channel_commands
        expiration_commands = user_doc.get("channel_token_commands_expiration")
        if expiration_commands and self.pubnub_client.is_token_expired(expiration_commands):
            new_token_commands, new_expiration_commands = self.pubnub_client.generate_token([user_doc["channel_name_commands"]])
            if new_token_commands:
                self.update_user_tokens(google_id, {
                    "channel_token_commands": new_token_commands,
                    "channel_token_commands_expiration": new_expiration_commands
                })
                tokens_updated = True

        # Перевірка та оновлення токенів для channel_status
        expiration_status = user_doc.get("channel_token_status_expiration")
        if expiration_status and self.pubnub_client.is_token_expired(expiration_status):
            new_token_status, new_expiration_status = self.pubnub_client.generate_token([user_doc["channel_name_status"]])
            if new_token_status:
                self.update_user_tokens(google_id, {
                    "channel_token_status": new_token_status,
                    "channel_token_status_expiration": new_expiration_status
                })
                tokens_updated = True

        return tokens_updated
    
    def get_all_users(self):
        return get_all_users()
