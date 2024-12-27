from pymongo import MongoClient
from datetime import datetime, timezone
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["party_sense_db"]

users_collection = db["users"]
playlists_collection = db["playlists"]
favorites_collection = db["favorites"]
categories_collection = db["categories"]
current_playback_collection = db["current_playback"]
playback_history_collection = db["playback_history"]

def create_indexes():
    try:
        existing_indexes = users_collection.index_information()
        if "google_id_1" not in existing_indexes:
            users_collection.create_index("google_id", unique=True)
            logger.info("Unique index on google_id created.")
        else:
            logger.info("Unique index on google_id already exists.")

        existing_playback_indexes = playback_history_collection.index_information()
        if "google_id_1_played_at_-1" not in existing_playback_indexes:
            playback_history_collection.create_index([("google_id", 1), ("played_at", -1)])
            logger.info("Compound index on playback_history created.")
        else:
            logger.info("Compound index on playback_history already exists.")

        existing_playlists_indexes = playlists_collection.index_information()
        if "google_id_1" not in existing_playlists_indexes:
            playlists_collection.create_index("google_id")
            logger.info("Index on google_id for playlists created.")
        else:
            logger.info("Index on google_id for playlists already exists.")

        existing_favorites_indexes = favorites_collection.index_information()
        if "google_id_1" not in existing_favorites_indexes:
            favorites_collection.create_index("google_id")
            logger.info("Index on google_id for favorites created.")
        else:
            logger.info("Index on google_id for favorites already exists.")

        existing_categories_indexes = categories_collection.index_information()
        if "google_id_1" not in existing_categories_indexes:
            categories_collection.create_index("google_id")
            logger.info("Index on google_id for categories created.")
        else:
            logger.info("Index on google_id for categories already exists.")

        existing_current_playback_indexes = current_playback_collection.index_information()
        if "google_id_1" not in existing_current_playback_indexes:
            current_playback_collection.create_index("google_id", unique=True)
            logger.info("Unique index on google_id for current_playback created.")
        else:
            logger.info("Unique index on google_id for current_playback already exists.")
    except Exception as e:
        logger.error(f"Error during creating indexes: {e}")

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

def create_playlist(google_id, name, description=""):
    playlist_doc = {
        "google_id": google_id,
        "name": name,
        "description": description,
        "songs": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    result = playlists_collection.insert_one(playlist_doc)
    return result.inserted_id

def update_playlist(playlist_id, update_data):
    update_data["updated_at"] = datetime.now(timezone.utc)
    playlists_collection.update_one(
        {"_id": playlist_id},
        {"$set": update_data}
    )

def get_playlists(google_id):
    return playlists_collection.find({"google_id": google_id})

def delete_playlist(google_id, playlist_id):
    result = playlists_collection.delete_one({"_id": playlist_id, "google_id": google_id})
    return result.deleted_count > 0

def create_favorites(google_id):
    favorites_doc = {
        "google_id": google_id,
        "songs": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    result = favorites_collection.insert_one(favorites_doc)
    return result.inserted_id

def add_favorite(google_id, song):
    favorites_collection.update_one(
        {"google_id": google_id},
        {"$push": {"songs": song}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )

def remove_favorite(google_id, video_id):
    favorites_collection.update_one(
        {"google_id": google_id},
        {"$pull": {"songs": {"video_id": video_id}}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )

def get_favorites(google_id):
    return favorites_collection.find_one({"google_id": google_id})

def create_category(google_id, name, description=""):
    category = {
        "name": name,
        "description": description,
        "playlists": []
    }
    categories_collection.update_one(
        {"google_id": google_id},
        {"$push": {"categories": category}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )

def add_playlist_to_category(google_id, category_name, playlist_id):
    categories_collection.update_one(
        {"google_id": google_id, "categories.name": category_name},
        {"$push": {"categories.$.playlists": playlist_id}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )

def get_categories(google_id):
    category_doc = categories_collection.find_one({"google_id": google_id}, {"categories": 1})
    return category_doc.get("categories") if category_doc else []

def get_current_playback(google_id):
    return current_playback_collection.find_one({"google_id": google_id})

def update_current_playback(google_id, current_song):
    current_playback_collection.update_one(
        {"google_id": google_id},
        {"$set": {"current_song": current_song}},
        upsert=True
    )
