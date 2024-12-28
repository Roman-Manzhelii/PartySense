import os
import requests
import logging
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"

def parse_iso8601_duration(iso_duration: str) -> int:
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, iso_duration)
    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds

def get_video_details(video_id):
    if not video_id:
        logger.warning("No video_id provided in get_video_details.")
        return None

    url = f"{BASE_URL}/videos"
    params = {
        "part": "snippet,contentDetails",
        "id": video_id,
        "key": YOUTUBE_API_KEY,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        if not items:
            logger.warning(f"No video details found for {video_id}")
            return None

        item = items[0]
        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})

        title = snippet.get("title", "Unknown Title")
        thumbs = snippet.get("thumbnails", {})
        if "high" in thumbs:
            thumb_url = thumbs["high"]["url"]
        elif "medium" in thumbs:
            thumb_url = thumbs["medium"]["url"]
        elif "default" in thumbs:
            thumb_url = thumbs["default"]["url"]
        else:
            thumb_url = ""

        iso_duration = content_details.get("duration", "PT0S")
        duration_seconds = parse_iso8601_duration(iso_duration)

        return {
            "title": title,
            "thumbnail_url": thumb_url,
            "duration_seconds": duration_seconds
        }

    except requests.RequestException as e:
        logger.error(f"Error fetching YouTube video details: {e}")
        return None

# Решта функцій без змін:
def search_youtube_music(query, max_results=20, page_token=None):
    url = f"{BASE_URL}/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoCategoryId": "10",
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
        "videoCategoryId": "10",
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
            vid = item["id"]["videoId"]
            if title not in unique_titles:
                unique_titles[title] = vid
        suggestions = [{"title": t, "video_id": v} for t, v in unique_titles.items()]
        logger.info(f"Fetched autocomplete suggestions for '{query}': {suggestions}")
        return suggestions
    except requests.RequestException as e:
        logger.error(f"Error fetching autocomplete suggestions: {e}")
        return []

def play_youtube_music(video_id):
    if not video_id:
        logger.error("No video ID for playing music.")
        return False
    logger.info(f"Playing YouTube music with video_id {video_id}.")
    return True

def control_music(action):
    if action not in ["pause", "resume", "next", "previous"]:
        logger.error(f"Unsupported action '{action}'.")
        return False
    logger.info(f"Controlling music with action '{action}'.")
    return True

def fetch_video_title(video_id):
    # Старий метод, можна залишити
    url = f"{BASE_URL}/videos"
    params = {"part": "snippet", "id": video_id, "key": YOUTUBE_API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        if items:
            title = items[0]["snippet"]["title"]
            logger.info(f"Fetched video title for {video_id}: {title}")
            return title
    except requests.RequestException as e:
        logger.error(f"Error fetching video title: {e}")
    return None
