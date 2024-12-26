# services/search_service.py
from youtube_api import search_youtube_music, autocomplete_music
import logging

logger = logging.getLogger(__name__)

class SearchService:
    def search_youtube_music(self, query, max_results=20, page_token=None):
        results = search_youtube_music(query, max_results, page_token)
        if results:
            logger.info(f"Search results fetched for query '{query}'.")
        else:
            logger.error(f"Failed to fetch search results for query '{query}'.")
        return results

    def autocomplete_music(self, query, max_results=3):
        suggestions = autocomplete_music(query, max_results)
        if suggestions:
            logger.info(f"Autocomplete suggestions fetched for query '{query}'.")
        else:
            logger.error(f"Failed to fetch autocomplete suggestions for query '{query}'.")
        return suggestions
