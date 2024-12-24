import os
import requests

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

    print(f"Requesting YouTube API with params: {params}")  # Додане логування

    response = requests.get(url, params=params)
    if response.status_code == 200:
        print("YouTube API response OK.")
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
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

    print(f"Requesting YouTube API for autocomplete with params: {params}")  # Додане логування

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        # Повертаємо лише унікальні заголовки
        unique_titles = {}
        for item in items:
            title = item["snippet"]["title"]
            video_id = item["id"]["videoId"]
            if title not in unique_titles:
                unique_titles[title] = video_id
        return [{"title": title, "video_id": vid} for title, vid in unique_titles.items()]
    print(f"Error fetching autocomplete suggestions: {response.status_code} - {response.text}")
    return []

def play_youtube_music(video_id):
    if not video_id:
        print("Error: No video ID provided.")
        return False

    print(f"Playing YouTube Music video with ID: {video_id}")
    return True

def control_music(action):
    if action not in ["pause", "resume", "next", "previous"]:
        print(f"Error: Unsupported action '{action}'")
        return False

    print(f"Music control action: {action}")
    return True

def fetch_video_title(video_id):
    url = f"{BASE_URL}/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YOUTUBE_API_KEY,
    }
    print(f"Fetching video title with params: {params}")  # Додане логування
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        if items:
            return items[0]["snippet"]["title"]
    print(f"Error fetching video title: {response.status_code} - {response.text}")
    return None
