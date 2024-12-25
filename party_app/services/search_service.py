# services/search_service.py
from youtube_api import search_youtube_music, autocomplete_music

class SearchService:
    def search_youtube_music(self, query, max_results=20, page_token=None):
        return search_youtube_music(query, max_results, page_token)

    def autocomplete_music(self, query, max_results=3):
        return autocomplete_music(query, max_results)
