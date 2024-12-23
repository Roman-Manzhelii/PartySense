import os
import requests

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"

def search_youtube_music(query, max_results=10):
    url = f"{BASE_URL}/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoCategoryId": "10",  # Category ID for Music
        "key": YOUTUBE_API_KEY,
        "maxResults": max_results,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

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
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        if items:
            return items[0]["snippet"]["title"]
    print(f"Error fetching video title: {response.status_code} - {response.text}")
    return None
