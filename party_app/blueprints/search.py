from flask import Blueprint, jsonify, request, redirect, session
from services.search_service import SearchService
import logging

search_bp = Blueprint('search', __name__)
search_service = SearchService()
logger = logging.getLogger(__name__)

@search_bp.route("/search", methods=["GET"])
def search_music():
    if "google_id" not in session:
        return redirect("/unauthorized")

    query = request.args.get("query", "")
    page_token = request.args.get("pageToken", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    logger.info(f"Search query: '{query}', Page token: '{page_token}'")
    try:
        results = search_service.search_youtube_music(query, page_token=page_token)
        if results:
            logger.info(f"Next Page Token: {results.get('nextPageToken')}")
            return jsonify(results)
        else:
            return jsonify({"error": "Failed to fetch results"}), 500
    except Exception as e:
        logger.error(f"Error during search: {e}")
        return jsonify({"error": "Internal server error"}), 500


@search_bp.route("/autocomplete", methods=["GET"])
def autocomplete():
    query = request.args.get("query", "")
    if not query:
        return jsonify([])

    suggestions = search_service.autocomplete_music(query)
    return jsonify(suggestions)
