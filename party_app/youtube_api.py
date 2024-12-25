# youtube_api.py
import os
import requests
import logging

logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"

def search_youtube_music(query, max_results=20, page_token=None):
    url = f"{BASE_URL}/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoCategoryId": "10",  # Category ID for Music
        "key": YOUTUBE_API_KEY,
        "maxResults": max_results,
    }
    if page_token:
        params["pageToken"] = page_token

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching YouTube search results: {e}")
        return None

def autocomplete_music(query, max_results=3):
    url = f"{BASE_URL}/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoCategoryId": "10",  # Category ID for Music
        "key": YOUTUBE_API_KEY,
        "maxResults": max_results,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        unique_titles = {}
        for item in items:
            title = item["snippet"]["title"]
            video_id = item["id"]["videoId"]
            if title not in unique_titles:
                unique_titles[title] = video_id
        return [{"title": title, "video_id": vid} for title, vid in unique_titles.items()]
    except requests.RequestException as e:
        logger.error(f"Error fetching autocomplete suggestions: {e}")
        return []

def play_youtube_music(video_id):
    if not video_id:
        logger.error("No video ID provided for playing music.")
        return False
    # Реалізація відтворення музики
    return True

def control_music(action):
    if action not in ["pause", "resume", "next", "previous"]:
        logger.error(f"Unsupported action '{action}' for music control.")
        return False
    # Реалізація контролю музики
    return True

def fetch_video_title(video_id):
    url = f"{BASE_URL}/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YOUTUBE_API_KEY,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        if items:
            return items[0]["snippet"]["title"]
    except requests.RequestException as e:
        logger.error(f"Error fetching video title: {e}")
    return None
