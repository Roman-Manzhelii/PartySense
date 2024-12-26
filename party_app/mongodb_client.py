# mongodb_client.py
from pymongo import MongoClient
from datetime import datetime, timezone
import os
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["party_sense_db"]

# Колекції
users_collection = db["users"]
playlists_collection = db["playlists"]
favorites_collection = db["favorites"]
categories_collection = db["categories"]
current_playback_collection = db["current_playback"]
playback_history_collection = db["playback_history"]

def create_indexes():
    try:
        # Інедексація для користувачів
        existing_indexes = users_collection.index_information()
        if "google_id_1" not in existing_indexes:
            users_collection.create_index("google_id", unique=True)
            logger.info("Unique index on google_id created.")
        else:
            logger.info("Unique index on google_id already exists.")

        # Інедексація для playback_history
        existing_playback_indexes = playback_history_collection.index_information()
        if "google_id_1_played_at_-1" not in existing_playback_indexes:
            playback_history_collection.create_index([("google_id", 1), ("played_at", -1)])
            logger.info("Compound index on playback_history created.")
        else:
            logger.info("Compound index on playback_history already exists.")

        # Інедексація для playlists
        existing_playlists_indexes = playlists_collection.index_information()
        if "user_id_1" not in existing_playlists_indexes:
            playlists_collection.create_index("user_id")
            logger.info("Index on user_id for playlists created.")
        else:
            logger.info("Index on user_id for playlists already exists.")

        # Інедексація для favorites
        existing_favorites_indexes = favorites_collection.index_information()
        if "user_id_1" not in existing_favorites_indexes:
            favorites_collection.create_index("user_id")
            logger.info("Index on user_id for favorites created.")
        else:
            logger.info("Index on user_id for favorites already exists.")

        # Інедексація для categories
        existing_categories_indexes = categories_collection.index_information()
        if "user_id_1" not in existing_categories_indexes:
            categories_collection.create_index("user_id")
            logger.info("Index on user_id for categories created.")
        else:
            logger.info("Index on user_id for categories already exists.")

        # Інедексація для current_playback
        existing_current_playback_indexes = current_playback_collection.index_information()
        if "user_id_1" not in existing_current_playback_indexes:
            current_playback_collection.create_index("user_id", unique=True)
            logger.info("Unique index on user_id for current_playback created.")
        else:
            logger.info("Unique index on user_id for current_playback already exists.")
    except Exception as e:
        logger.error(f"Error during creating indexes: {e}")

# Функції для користувачів
def get_user_by_google_id(google_id):
    return users_collection.find_one({"google_id": google_id})

def save_user(user_doc):
    users_collection.insert_one(user_doc)

def update_user_token(google_id, tokens):
    users_collection.update_one(
        {"google_id": google_id},
        {"$set": tokens}
    )

def save_preferences(google_id, preferences):
    users_collection.update_one(
        {"google_id": google_id},
        {"$set": {"preferences": preferences}},
        upsert=True
    )

def get_preferences(google_id):
    user = users_collection.find_one({"google_id": google_id}, {"preferences": 1})
    return user.get("preferences") if user else None

def log_playback_history(google_id, video_id, title):
    playback_history_collection.insert_one({
        "google_id": google_id,
        "video_id": video_id,
        "title": title,
        "played_at": datetime.now(timezone.utc)
    })

def get_all_users():
    return users_collection.find({})

# Функції для плейлистів
def create_playlist(user_id, name, description=""):
    playlist_doc = {
        "user_id": user_id,
        "name": name,
        "description": description,
        "songs": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    result = playlists_collection.insert_one(playlist_doc)
    playlists_collection.update_one(
        {"_id": result.inserted_id},
        {"$push": {"songs": {"$each": []}}}
    )
    return result.inserted_id

def update_playlist(playlist_id, update_data):
    update_data["updated_at"] = datetime.now(timezone.utc)
    playlists_collection.update_one(
        {"_id": playlist_id},
        {"$set": update_data}
    )

def get_playlists(user_id):
    return playlists_collection.find({"user_id": user_id})

def delete_playlist(user_id, playlist_id):
    result = playlists_collection.delete_one({"_id": playlist_id, "user_id": user_id})
    return result.deleted_count > 0

# Функції для улюблених пісень
def create_favorites(user_id):
    favorites_doc = {
        "user_id": user_id,
        "songs": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    result = favorites_collection.insert_one(favorites_doc)
    return result.inserted_id

def add_favorite(user_id, song):
    favorites_collection.update_one(
        {"user_id": user_id},
        {"$push": {"songs": song}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )

def remove_favorite(user_id, video_id):
    favorites_collection.update_one(
        {"user_id": user_id},
        {"$pull": {"songs": {"video_id": video_id}}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )

def get_favorites(user_id):
    return favorites_collection.find_one({"user_id": user_id})

# Функції для категорій
def create_category(user_id, name, description=""):
    category = {
        "name": name,
        "description": description,
        "playlists": []
    }
    categories_collection.update_one(
        {"user_id": user_id},
        {"$push": {"categories": category}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )

def add_playlist_to_category(user_id, category_name, playlist_id):
    categories_collection.update_one(
        {"user_id": user_id, "categories.name": category_name},
        {"$push": {"categories.$.playlists": playlist_id}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )

def get_categories(user_id):
    category_doc = categories_collection.find_one({"user_id": user_id}, {"categories": 1})
    return category_doc.get("categories") if category_doc else []

# Функції для поточного відтворення
def get_current_playback(user_id):
    return current_playback_collection.find_one({"user_id": user_id})

def update_current_playback(user_id, current_song):
    current_playback_collection.update_one(
        {"user_id": user_id},
        {"$set": {"current_song": current_song}},
        upsert=True
    )
