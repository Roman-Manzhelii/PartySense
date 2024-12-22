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


def get_user_playlists():
    url = f"{BASE_URL}/playlists"
    params = {
        "part": "snippet,contentDetails",
        "mine": True,
        "key": YOUTUBE_API_KEY,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def play_youtube_music(video_id):
    """
    Mock function to simulate playing YouTube Music.
    Replace this with actual playback logic if required.
    """
    if not video_id:
        print("Error: No video ID provided.")
        return False

    # Simulate sending a request to a playback service or device
    print(f"Playing YouTube Music video with ID: {video_id}")
    # Example logic: Return True as a success mock
    return True
