# mongodb_client.py
from pymongo import MongoClient
from datetime import datetime, timezone
import os

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["party_sense_db"]

# Колекції
users_collection = db["users"]
playback_history_collection = db["playback_history"]

def create_indexes():
    try:
        # Перевірка чи індекс вже існує
        existing_indexes = users_collection.index_information()
        if "google_id_1" not in existing_indexes:
            users_collection.create_index("google_id", unique=True)
            print("Unique index on google_id created.")
        else:
            print("Unique index on google_id already exists.")

        existing_playback_indexes = playback_history_collection.index_information()
        if "google_id_1_played_at_-1" not in existing_playback_indexes:
            playback_history_collection.create_index([("google_id", 1), ("played_at", -1)])
            print("Compound index on playback_history created.")
        else:
            print("Compound index on playback_history already exists.")
    except Exception as e:
        print(f"Error during creating indexes: {e}")

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
