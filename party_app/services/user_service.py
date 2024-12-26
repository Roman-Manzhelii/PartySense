# services/user_service.py
from mongodb_client import (
    get_user_by_google_id,
    save_user,
    save_preferences,
    get_preferences,
    log_playback_history,
    update_user_token,
    get_all_users,
    create_playlist,
    update_playlist,
    get_playlists,
    delete_playlist,
    add_favorite,
    remove_favorite,
    create_favorites,
    get_favorites,
    create_category,
    add_playlist_to_category,
    get_categories,
    get_current_playback,
    update_current_playback,
)
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, pubnub_client):
        self.pubnub_client = pubnub_client

    # Користувачі
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
                logger.info(f"Updated channel_token_commands for user {google_id}")
            else:
                logger.error("Failed to update channel_token_commands.")
                return False

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
                logger.info(f"Updated channel_token_status for user {google_id}")
            else:
                logger.error("Failed to update channel_token_status.")
                return False

        return tokens_updated

    def get_all_users(self):
        return get_all_users()

    # Плейлисти
    def create_playlist(self, user_id, name, description=""):
        playlist_id = create_playlist(user_id, name, description)
        logger.info(f"Created playlist '{name}' with ID {playlist_id} for user {user_id}.")
        return playlist_id

    def update_playlist(self, playlist_id, update_data):
        update_playlist(playlist_id, update_data)
        logger.info(f"Updated playlist {playlist_id} with data {update_data}.")

    def get_playlists(self, user_id):
        return get_playlists(user_id)

    def delete_playlist(self, user_id, playlist_id):
        success = delete_playlist(user_id, playlist_id)
        if success:
            logger.info(f"Deleted playlist {playlist_id} for user {user_id}.")
        else:
            logger.warning(f"Failed to delete playlist {playlist_id} for user {user_id}.")
        return success

    # Улюблені пісні
    def create_favorites(self, user_id):
        favorites_id = create_favorites(user_id)
        logger.info(f"Created favorites with ID {favorites_id} for user {user_id}.")
        return favorites_id

    def add_favorite(self, user_id, song):
        add_favorite(user_id, song)
        logger.info(f"Added song {song['video_id']} to favorites for user {user_id}.")

    def remove_favorite(self, user_id, video_id):
        remove_favorite(user_id, video_id)
        logger.info(f"Removed song {video_id} from favorites for user {user_id}.")

    def get_favorites(self, user_id):
        return get_favorites(user_id)

    # Категорії
    def create_category(self, user_id, name, description=""):
        create_category(user_id, name, description)
        logger.info(f"Created category '{name}' for user {user_id}.")

    def add_playlist_to_category(self, user_id, category_name, playlist_id):
        add_playlist_to_category(user_id, category_name, playlist_id)
        logger.info(f"Added playlist {playlist_id} to category '{category_name}' for user {user_id}.")

    def get_categories(self, user_id):
        return get_categories(user_id)

    # Поточне відтворення
    def get_current_playback(self, user_id):
        return get_current_playback(user_id)

    def update_current_playback(self, user_id, current_song):
        update_current_playback(user_id, current_song)
        logger.info(f"Updated current playback for user {user_id} with song {current_song.get('video_id')}.")
