// search.js
import { API } from './api.js';
import { debounce } from './helpers.js';
import { playSongFromSearch } from './playback/playbackActions.js';

let nextPageToken = null;
let isLoading = false;
let currentQuery = "";
const loadedVideoIds = new Set();

export function setupSearch() {
  const searchInput = document.getElementById("search");
  const suggestionsList = document.getElementById("autocomplete-suggestions");
  const searchBtn = document.getElementById("search-btn");

  if (searchBtn) {
    searchBtn.addEventListener("click", () => {
      if (searchInput) {
        initiateSearch(searchInput.value.trim());
      }
    });
  }

  const debouncedAutocomplete = debounce(() => {
    if (!searchInput) return;
    const query = searchInput.value.trim();
    if (query.length < 2) {
      suggestionsList.innerHTML = "";
      suggestionsList.classList.remove("show");
      return;
    }
    fetch(`${API.AUTOCOMPLETE}?query=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(data => {
        updateSuggestionsUI(data, searchInput, suggestionsList);
      })
      .catch(err => console.error("Autocomplete error:", err));
  }, 300);

  if (searchInput) {
    searchInput.addEventListener("input", debouncedAutocomplete);
    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        initiateSearch(searchInput.value.trim());
      }
    });
  }

  window.addEventListener("scroll", debounce(() => {
    if (isLoading || !nextPageToken) return;
    const pinned = document.getElementById("playback-status");
    const pinnedHeight = pinned ? pinned.offsetHeight : 0;
    if ((window.innerHeight + window.scrollY) >= (document.body.offsetHeight - pinnedHeight - 50)) {
      fetchResults(currentQuery);
    }
  }, 200));

  document.addEventListener("click", (evt) => {
    if (!suggestionsList) return;
    if (!suggestionsList.contains(evt.target) && evt.target !== searchInput) {
      suggestionsList.innerHTML = "";
      suggestionsList.classList.remove("show");
    }
  });
}

function updateSuggestionsUI(suggestions, searchInput, suggestionsList) {
  if (!suggestionsList) return;
  if (!suggestions || suggestions.length === 0) {
    suggestionsList.innerHTML = "";
    suggestionsList.classList.remove("show");
    return;
  }
  suggestionsList.innerHTML = "";
  suggestionsList.classList.add("show");

  suggestions.forEach(({ title }) => {
    const li = document.createElement("li");
    li.className = "suggestion-item";
    li.textContent = title;
    li.addEventListener("click", () => {
      searchInput.value = title;
      suggestionsList.innerHTML = "";
      suggestionsList.classList.remove("show");
      initiateSearch(title);
    });
    suggestionsList.appendChild(li);
  });
}

export function initiateSearch(query) {
  if (!query) {
    alert("Please enter a search query.");
    return;
  }
  currentQuery = query;
  nextPageToken = null;
  loadedVideoIds.clear();

  const resultsGrid = document.getElementById("results-grid");
  if (resultsGrid) resultsGrid.innerHTML = "";

  fetchResults(query);
}

function fetchResults(query) {
  if (!query || isLoading) return;
  isLoading = true;
  updateLoadingIndicator(true);

  let url = `${API.SEARCH}?query=${encodeURIComponent(query)}`;
  if (nextPageToken) {
    url += `&pageToken=${encodeURIComponent(nextPageToken)}`;
  }

  fetch(url)
    .then(res => res.json())
    .then(data => {
      nextPageToken = data.nextPageToken || null;
      renderSearchResults(data);
    })
    .catch(err => console.error("Search error:", err))
    .finally(() => {
      isLoading = false;
      updateLoadingIndicator(false);
    });
}

function renderSearchResults(data) {
  const resultsGrid = document.getElementById("results-grid");
  if (!resultsGrid) return;

  (data.items || []).forEach(({ snippet, id }) => {
    if (!id || !snippet) return;
    if (loadedVideoIds.has(id.videoId)) return;
    loadedVideoIds.add(id.videoId);

    const card = document.createElement("div");
    card.className = "result-card";

    const img = document.createElement("img");
    img.src = snippet.thumbnails.medium.url;
    img.alt = snippet.title;

    const titleElem = document.createElement("h4");
    titleElem.textContent = snippet.title;

    card.addEventListener("click", () => {
      playSongFromSearch({
        video_id: id.videoId,
        title: snippet.title,
        thumbnail_url: snippet.thumbnails.medium.url,
        duration: 0
      });
    });

    card.appendChild(img);
    card.appendChild(titleElem);
    resultsGrid.appendChild(card);
  });
}

function updateLoadingIndicator(show) {
  const loadingEl = document.getElementById("loading");
  if (!loadingEl) return;
  loadingEl.style.display = show ? "block" : "none";
}