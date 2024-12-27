const API = {
    SEARCH: "/search",
    AUTOCOMPLETE: "/autocomplete",
    CONTROL: "/control_music",
    PLAYLISTS: "/api/playlists",
    FAVORITES: "/api/favorites",
    CATEGORIES: "/api/categories",
    PLAYBACK: "/api/playback"
};

let nextPageToken = null;
let isLoading = false;
let currentQuery = "";
const loadedVideoIds = new Set();

/**
 * Position & Duration for the UI slider in playback:
 */
let currentDuration = 0;
let currentPosition = 0;
let currentPlayingState = "paused";

document.addEventListener("DOMContentLoaded", () => {
  // 1) Lottie
  const container = document.getElementById("lottie-container");
  if (container) {
    lottie.loadAnimation({
      container: container,
      renderer: 'svg',
      loop: true,
      autoplay: true,
      path: '/static/lottie/gradient.json'
    });
  }

  // 2) Setup search + autocomplete
  setupSearch();

  // 3) Socket
  setupSocket();

  // 4) Playback UI (shuffle, prev, play/pause, next, repeat, slider)
  setupPlaybackUI();
});

/* ========== Helpers ========== */
function debounce(fn, delay) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), delay);
  };
}

/* ========== 1. Search & Autocomplete ========== */
function setupSearch() {
  const searchInput = document.getElementById("search");
  const suggestionsList = document.getElementById("autocomplete-suggestions");

  const debouncedAutocomplete = debounce(() => {
    handleAutocomplete(searchInput, suggestionsList);
  }, 300);

  searchInput.addEventListener("input", debouncedAutocomplete);

  // Enter => start search
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      initiateSearch(searchInput.value.trim());
    }
  });

  // Pagination with pinned playback
  window.addEventListener("scroll", debounce(() => {
    if (isLoading || !nextPageToken) return;
    const pinned = document.getElementById("playback-status");
    const pinnedHeight = pinned ? pinned.offsetHeight : 0;
    if ((window.innerHeight + window.scrollY) >= (document.body.offsetHeight - pinnedHeight - 50)) {
      fetchResults(currentQuery);
    }
  }, 200));

  // Close suggestions if clicked outside
  document.addEventListener("click", (evt) => {
    if (!suggestionsList.contains(evt.target) && evt.target !== searchInput) {
      suggestionsList.innerHTML = "";
    }
  });
}

function handleAutocomplete(searchInput, suggestionsList) {
  const query = searchInput.value.trim();
  if (query.length < 2) {
    suggestionsList.innerHTML = "";
    return;
  }

  fetch(`${API.AUTOCOMPLETE}?query=${encodeURIComponent(query)}`)
    .then((res) => res.json())
    .then((data) => {
      updateSuggestionsUI(data, searchInput, suggestionsList);
    })
    .catch((err) => console.error("Autocomplete error:", err));
}

function updateSuggestionsUI(suggestions, searchInput, suggestionsList) {
  suggestionsList.innerHTML = "";
  suggestions.forEach(({ title }) => {
    const li = document.createElement("li");
    li.className = "suggestion-item";
    li.textContent = title;
    li.addEventListener("click", () => {
      searchInput.value = title;
      suggestionsList.innerHTML = "";
      initiateSearch(title);
    });
    suggestionsList.appendChild(li);
  });
}

function searchMusic() {
  const val = document.getElementById("search").value.trim();
  initiateSearch(val);
}

function initiateSearch(query) {
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

/* ========== 2. Socket ========== */
function setupSocket() {
  const socket = io();
  socket.on("connect", () => console.log("Socket connected"));
  socket.on("playback_update", (data) => {
    console.log("playback_update:", data);
    updatePlaybackUI(data);
  });
  socket.on("disconnect", () => console.log("Socket disconnected"));
}

/* ========== 3. Playback, Favorites, Current Playback ========== */

/** 
 * Ініціалізація нових кнопок: shuffle, prev, play/pause, next, repeat + прогрес-бар
 */
function setupPlaybackUI() {
  const shuffleBtn = document.getElementById("btn-shuffle");
  const prevBtn = document.getElementById("btn-prev");
  const playPauseBtn = document.getElementById("btn-play-pause");
  const nextBtn = document.getElementById("btn-next");
  const repeatBtn = document.getElementById("btn-repeat");

  shuffleBtn?.addEventListener("click", () => {
    // set_mode => shuffle
    fetch(API.PLAYBACK, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "set_mode",
        mode: "shuffle"
      })
    });
  });

  prevBtn?.addEventListener("click", () => {
    sendControlAction("previous");
  });

  playPauseBtn?.addEventListener("click", () => {
    if (currentPlayingState === "playing") {
      // Pause
      sendPauseCommand();
    } else {
      // Resume
      sendResumeCommand();
    }
  });

  nextBtn?.addEventListener("click", () => {
    sendControlAction("next");
  });

  repeatBtn?.addEventListener("click", () => {
    // set_mode => repeat
    fetch(API.PLAYBACK, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "set_mode",
        mode: "repeat"
      })
    });
  });

  const progressSlider = document.getElementById("playback-progress");
  progressSlider?.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    currentPosition = val;
  });
  // On "change" => відправляємо seek
  progressSlider?.addEventListener("change", (e) => {
    const val = parseFloat(e.target.value);
    sendSeekCommand(val);
  });
}

function sendControlAction(action) {
  fetch(API.CONTROL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action })
  })
  .then(res => res.json())
  .then(data => {
    if (!data.success) {
      console.error(data.error || "Music control error");
    }
  })
  .catch(err => console.error("controlMusic error:", err));
}

function sendPauseCommand() {
  const nowTs = Date.now();
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "pause",
      position: currentPosition,
      timestamp: nowTs
    })
  });
}

function sendResumeCommand() {
  const nowTs = Date.now();
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "resume",
      position: currentPosition,
      timestamp: nowTs
    })
  });
}

function sendSeekCommand(newPos) {
  const nowTs = Date.now();
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "seek",
      position: newPos,
      timestamp: nowTs
    })
  });
}

function playSongFromSearch(songData) {
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "play",
      video_id: songData.video_id,
      title: songData.title,
      thumbnail_url: songData.thumbnail_url,
      duration: songData.duration,
      position: 0,
      mode: "default",
      timestamp: Date.now()
    })
  })
  .then(res => res.json())
  .then(resp => {
    console.log("Play from search:", resp);
    updateCurrentPlaybackUI(songData, "playing", 0);
  })
  .catch(err => console.error("playSongFromSearch error:", err));
}

function playSongFromFavorites(btn) {
  const li = btn.closest(".favorite-item");
  if (!li) return;

  const video_id = li.dataset.videoId;
  const title = li.dataset.title;
  const thumbnail = li.dataset.thumbnail;
  const duration = parseInt(li.dataset.duration || "0");

  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "play",
      video_id,
      title,
      thumbnail_url: thumbnail,
      duration,
      position: 0,
      mode: "default",
      timestamp: Date.now()
    })
  })
  .then(res => res.json())
  .then(data => {
    console.log("Playing favorite:", data);
    updateCurrentPlaybackUI({ video_id, title, thumbnail_url: thumbnail, duration }, "playing", 0);
  })
  .catch(err => console.error("playSongFromFavorites error:", err));
}

/* Fav UI updates */
function updateFavoritesUI_afterAdd(song) {
  const favList = document.getElementById("favorites-list");
  if (!favList) return;

  const li = document.createElement("li");
  li.className = "favorite-item";
  li.dataset.videoId = song.video_id;
  li.dataset.title = song.title;
  li.dataset.thumbnail = song.thumbnail_url || "";
  li.dataset.duration = song.duration || 0;

  const spanTitle = document.createElement("span");
  spanTitle.className = "song-title";
  spanTitle.textContent = song.title;

  const heartBtn = document.createElement("button");
  heartBtn.className = "heart-btn";
  heartBtn.textContent = "♥";
  heartBtn.addEventListener("click", () => toggleFavorite(song.video_id));

  const playBtn = document.createElement("button");
  playBtn.className = "play-btn";
  playBtn.textContent = "Play";
  playBtn.addEventListener("click", () => playSongFromFavorites(playBtn));

  li.appendChild(spanTitle);
  li.appendChild(heartBtn);
  li.appendChild(playBtn);

  favList.appendChild(li);
}

function removeFavoriteUI(video_id) {
  const li = document.querySelector(`.favorite-item[data-video-id="${video_id}"]`);
  if (li) li.remove();
}

/* Current Playback UI local update */
function updateCurrentPlaybackUI(songData, state, pos) {
  document.getElementById("current-song-title").textContent = songData.title || "Unknown";
  currentDuration = songData.duration || 0;
  currentPosition = pos || 0;
  currentPlayingState = state;

  // If there's a slider, update max & value
  const slider = document.getElementById("playback-progress");
  if (slider) {
    slider.max = currentDuration;
    slider.value = currentPosition;
  }

  document.getElementById("playback-state").textContent = state;
  document.getElementById("playback-position").textContent = `${pos} sec`;

  window.__currentPlaybackId = songData.video_id || "";
  checkIfFavorite(window.__currentPlaybackId);

  // Update play/pause button icon
  const playPauseBtn = document.getElementById("btn-play-pause");
  if (playPauseBtn) {
    playPauseBtn.textContent = (state === "playing") ? "⏸" : "▶";
  }
}

/** Перевіряємо чи поточний трек у favorites */
function checkIfFavorite(video_id) {
  if (!video_id) return;
  fetch(API.FAVORITES)
    .then(res => res.json())
    .then(data => {
      const { favorites } = data;
      const isFav = favorites.some(s => s.video_id === video_id);
      const heartBtn = document.getElementById("current-heart-btn");
      if (heartBtn) {
        heartBtn.textContent = isFav ? "♥" : "♡";
      }
    })
    .catch(err => console.error("checkIfFavorite error:", err));
}

function toggleFavoriteInPlayback() {
  const vid = window.__currentPlaybackId;
  if (!vid) return;
  toggleFavorite(vid);
}

/** Якщо є => remove, якщо немає => add */
function toggleFavorite(video_id) {
  fetch(API.FAVORITES)
    .then(res => res.json())
    .then(data => {
      const { favorites } = data;
      const isInFav = favorites.some(s => s.video_id === video_id);
      if (isInFav) {
        removeFavorite(video_id);
      } else {
        addFavorite(video_id);
      }
    })
    .catch(err => console.error("toggleFavorite fetch error:", err));
}

function addFavorite(video_id) {
  const title = document.getElementById("current-song-title").textContent || "Unknown Title";
  const songObj = {
    video_id,
    title,
    thumbnail_url: "",
    duration: currentDuration,
    added_at: new Date().toISOString()
  };

  fetch(API.FAVORITES, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(songObj)
  })
  .then(res => res.json())
  .then(() => {
    document.getElementById("current-heart-btn").textContent = "♥";
    alert(`Song '${title}' added to favorites.`);
    updateFavoritesUI_afterAdd(songObj);
  })
  .catch(err => console.error("addFavorite error:", err));
}

function removeFavorite(video_id) {
  fetch(`${API.FAVORITES}/${video_id}`, { method: "DELETE" })
    .then(res => res.json())
    .then(() => {
      document.getElementById("current-heart-btn").textContent = "♡";
      alert(`Song removed from favorites.`);
      removeFavoriteUI(video_id);
    })
    .catch(err => console.error("removeFavorite error:", err));
}

/* Called by socket.io to reflect real-time changes from server */
function updatePlaybackUI(data) {
  if (!data || !data.current_song) return;
  const { video_id, title, state, position, duration } = data.current_song;

  currentPlayingState = state;
  currentPosition = position || 0;
  currentDuration = duration || 0;

  document.getElementById("current-song-title").textContent = title || "N/A";
  document.getElementById("playback-state").textContent = state || "Stopped";
  document.getElementById("playback-position").textContent = `${currentPosition} sec`;
  window.__currentPlaybackId = video_id || "";

  const slider = document.getElementById("playback-progress");
  if (slider) {
    slider.max = currentDuration;
    slider.value = currentPosition;
  }

  const playPauseBtn = document.getElementById("btn-play-pause");
  if (playPauseBtn) {
    playPauseBtn.textContent = (state === "playing") ? "⏸" : "▶";
  }

  checkIfFavorite(video_id);
}
