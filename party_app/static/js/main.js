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

// Ініціалізація
document.addEventListener("DOMContentLoaded", () => {
  // Запускаємо Lottie (якщо є контейнер)
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

  setupSearch();
  setupSocket();
});

/* ========== Helpers ========== */
function debounce(fn, delay) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), delay);
  };
}

/* ========== 1. Пошук + автодоповнення ========== */
function setupSearch() {
  const searchInput = document.getElementById("search");
  const suggestionsList = document.getElementById("autocomplete-suggestions");

  const debouncedAutocomplete = debounce(() => {
    handleAutocomplete(searchInput, suggestionsList);
  }, 300);

  searchInput.addEventListener("input", debouncedAutocomplete);

  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      initiateSearch(searchInput.value.trim());
    }
  });

  // Пагінація
  window.addEventListener("scroll", debounce(() => {
    if (isLoading || !nextPageToken) return;
    // Замість (document.body.offsetHeight - 100) врахуємо відступ зверху pinned playback
    const pinned = document.getElementById("playback-status");
    const pinnedHeight = pinned ? pinned.offsetHeight : 0;

    if ((window.innerHeight + window.scrollY) >= (document.body.offsetHeight - pinnedHeight - 50)) {
      fetchResults(currentQuery);
    }
  }, 200));

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
    .then(res => res.json())
    .then(data => {
      updateSuggestionsUI(data, searchInput, suggestionsList);
    })
    .catch(err => console.error("Autocomplete error:", err));
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

    // Клік => виклик "play"
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

/* ========== 3. Відтворення, Favorites, Current Playback ========== */
function controlMusic(action) {
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

function playSongFromSearch(songData) {
  // Відправляємо PLAY
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
      mode: "default"
    })
  })
  .then(res => res.json())
  .then(resp => {
    console.log("Play from search:", resp);
    updateCurrentPlaybackUI(songData, "playing", 0);
  })
  .catch(err => console.error("playSongFromSearch error:", err));
}

// Граємо з Favorites
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
      mode: "default"
    })
  })
  .then(res => res.json())
  .then(data => {
    console.log("Playing favorite:", data);
    updateCurrentPlaybackUI({ video_id, title, thumbnail_url: thumbnail, duration }, "playing", 0);
  })
  .catch(err => console.error("playSongFromFavorites error:", err));
}

// Оновлюємо Current Playback (локально)
function updateCurrentPlaybackUI(songData, state, position) {
  document.getElementById("current-song-title").textContent = songData.title || "Unknown";
  document.getElementById("playback-state").textContent = state || "Stopped";
  document.getElementById("playback-position").textContent = `${position} sec`;

  // Зберігаємо ID
  window.__currentPlaybackId = songData.video_id || "";
  checkIfFavorite(window.__currentPlaybackId);
}

// Перевіряємо, чи трек у фаворитах => змінюємо сердечко
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

// Тогл: якщо є => remove, якщо немає => add
function toggleFavorite(video_id) {
  fetch(API.FAVORITES)
    .then(res => res.json())
    .then(data => {
      const { favorites } = data;
      const isInFav = favorites.some(s => s.video_id === video_id);
      if (isInFav) removeFavorite(video_id);
      else addFavorite(video_id);
    })
    .catch(err => console.error("toggleFavorite fetch error:", err));
}

function addFavorite(video_id) {
  const title = document.getElementById("current-song-title").textContent || "Unknown Title";
  const thumbnail_url = "";
  const duration = 0;

  fetch(API.FAVORITES, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      video_id, title, thumbnail_url, duration, added_at: new Date().toISOString()
    })
  })
  .then(res => res.json())
  .then(() => {
    document.getElementById("current-heart-btn").textContent = "♥";
    alert(`Song '${title}' added to favorites.`);
  })
  .catch(err => console.error("addFavorite error:", err));
}

function removeFavorite(video_id) {
  fetch(`${API.FAVORITES}/${video_id}`, { method: "DELETE" })
    .then(res => res.json())
    .then(() => {
      document.getElementById("current-heart-btn").textContent = "♡";
      alert(`Song removed from favorites.`);
      // Видаляємо з DOM у списку
      const li = document.querySelector(`.favorite-item[data-video-id="${video_id}"]`);
      if (li) li.remove();
    })
    .catch(err => console.error("removeFavorite error:", err));
}

/* ========== 4. Socket playback_update callback ========== */
function updatePlaybackUI(data) {
  if (!data || !data.current_song) return;
  const { video_id, title, state, position } = data.current_song;

  document.getElementById("current-song-title").textContent = title || "N/A";
  document.getElementById("playback-state").textContent = state || "Stopped";
  document.getElementById("playback-position").textContent = `${position} sec`;

  window.__currentPlaybackId = video_id || "";
  checkIfFavorite(video_id);
}
