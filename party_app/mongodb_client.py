from pymongo import MongoClient
from datetime import datetime, timezone
import os

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["party_sense_db"]

# Collections
users_collection = db["users"]
preferences_collection = db["preferences"]
playback_history_collection = db["playback_history"]

def get_user_by_google_id(google_id):
    return users_collection.find_one({"google_id": google_id})

def save_preferences(google_id, volume, led_mode):
    preferences_collection.update_one(
        {"google_id": google_id},
        {"$set": {"volume": volume, "led_mode": led_mode}},
        upsert=True
    )

def get_preferences(google_id):
    return preferences_collection.find_one({"google_id": google_id})

def log_playback_history(google_id, video_id, title):
    playback_history_collection.insert_one({
        "google_id": google_id,
        "video_id": video_id,
        "title": title,
        "played_at": datetime.now(timezone.utc)
    })

def update_user_token(google_id, new_token):
    users_collection.update_one(
        {"google_id": google_id},
        {"$set": {"channel_token": new_token}}
    )

def save_user(user_doc):
    users_collection.insert_one(user_doc)
