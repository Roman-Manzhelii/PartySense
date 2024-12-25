# services/music_service.py
from youtube_api import (
    search_youtube_music,
    play_youtube_music,
    control_music as control_music_func,
    fetch_video_title,
    autocomplete_music
)

class MusicService:
    def search_youtube_music(self, query, max_results=20, page_token=None):
        return search_youtube_music(query, max_results, page_token)

    def autocomplete_music(self, query, max_results=3):
        return autocomplete_music(query, max_results)

    def play_youtube_music(self, video_id):
        return play_youtube_music(video_id)

    def control_music(self, action):
        return control_music_func(action)

    def fetch_video_title(self, video_id):
        return fetch_video_title(video_id)
