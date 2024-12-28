const API = {
  SEARCH: "/search",
  AUTOCOMPLETE: "/autocomplete",
  CONTROL: "/control_music",
  PLAYLISTS: "/api/playlists",
  FAVORITES: "/api/favorites",
  CATEGORIES: "/api/categories",
  PLAYBACK: "/api/playback",
  PREFERENCES: "/api/preferences"
};

let nextPageToken = null;
let isLoading = false;
let currentQuery = "";
const loadedVideoIds = new Set();

// Playback state
let currentDuration = 0;
let currentPosition = 0;
let currentPlayingState = "paused";

/* ========== 0. Helpers ========== */
/**
* debounce(fn, delay) — викликає fn лише після того, як 
* користувач перестане "спамити" (наприклад, input/scroll),
* витримавши паузу у delay мілісекунд.
*/
function debounce(fn, delay) {
let timeout;
return (...args) => {
  clearTimeout(timeout);
  timeout = setTimeout(() => fn.apply(this, args), delay);
};
}

/* ========== DOM READY ========== */
document.addEventListener("DOMContentLoaded", () => {
// 1) Lottie
initLottie();

// 2) Search + autocomplete
setupSearch();

// 3) Socket
setupSocket();

// 4) Playback controls + progress
setupPlaybackUI();

// 5) Profile menu (LED, motion)
initProfileMenuUI();

// 6) Volume slider
initVolumeUI();

// 7) Toggle profile dropdown on click
initProfileDropdownToggle();
});

/* ========== 1. Lottie ========== */
function initLottie() {
const container = document.getElementById("lottie-container");
if (container) {
  lottie.loadAnimation({
    container: container,
    renderer: 'svg',
    loop: true,
    autoplay: true,
    path: '/static/lottie/gradient2.json'
  });
}

const containerBottom = document.getElementById("lottie-container-bottom");
if (containerBottom) {
  lottie.loadAnimation({
    container: containerBottom,
    renderer: 'svg',
    loop: true,
    autoplay: true,
    path: '/static/lottie/gradient2.json'
  });
}
}

/* ========== 2. Search & Autocomplete ========== */
function setupSearch() {
const searchInput = document.getElementById("search");
const suggestionsList = document.getElementById("autocomplete-suggestions");

const debouncedAutocomplete = debounce(() => {
  if (!searchInput) return;
  const query = searchInput.value.trim();
  if (query.length < 2) {
    // сховати
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

  // Enter => search
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      initiateSearch(searchInput.value.trim());
    }
  });
}

// Infinity scroll (підвантаження результатів)
window.addEventListener("scroll", debounce(() => {
  if (isLoading || !nextPageToken) return;
  const pinned = document.getElementById("playback-status");
  const pinnedHeight = pinned ? pinned.offsetHeight : 0;
  if ((window.innerHeight + window.scrollY) >= (document.body.offsetHeight - pinnedHeight - 50)) {
    fetchResults(currentQuery);
  }
}, 200));

// Закриваємо пропозиції, якщо клік поза ними
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

/* ========== 3. Socket ========== */
function setupSocket() {
const socket = io();
socket.on("connect", () => console.log("Socket connected"));
socket.on("playback_update", (data) => {
  console.log("playback_update:", data);
  updatePlaybackUI(data);
});
socket.on("disconnect", () => console.log("Socket disconnected"));
}

/* ========== 4. Playback & Favorites ========== */
function setupPlaybackUI() {
const shuffleBtn = document.getElementById("btn-shuffle");
const prevBtn = document.getElementById("btn-prev");
const playPauseBtn = document.getElementById("btn-play-pause");
const nextBtn = document.getElementById("btn-next");
const repeatBtn = document.getElementById("btn-repeat");

shuffleBtn?.addEventListener("click", () => {
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "set_mode", mode: "shuffle" })
  });
});

prevBtn?.addEventListener("click", () => {
  sendControlAction("previous");
});

playPauseBtn?.addEventListener("click", () => {
  if (currentPlayingState === "playing") {
    sendPauseCommand();
  } else {
    sendResumeCommand();
  }
});

nextBtn?.addEventListener("click", () => {
  sendControlAction("next");
});

repeatBtn?.addEventListener("click", () => {
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "set_mode", mode: "repeat" })
  });
});

const progressSlider = document.getElementById("playback-progress");
if (progressSlider) {
  progressSlider.addEventListener("input", (e) => {
    currentPosition = parseFloat(e.target.value);
  });
  progressSlider.addEventListener("change", (e) => {
    sendSeekCommand(parseFloat(e.target.value));
  });
}
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
  .then(() => {
    updateCurrentPlaybackUI(songData, "playing", 0);
  })
  .catch(err => console.error("playSongFromSearch error:", err));
}

/* Favorites logic */
function playSongFromFavorites(btn) {
const li = btn.closest(".favorite-item");
if (!li) return;

const video_id = li.dataset.videoId;
const title = li.dataset.title;
const thumbnail = li.dataset.thumbnail;
const duration = parseInt(li.dataset.duration || "0", 10);

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
  .then(() => {
    updateCurrentPlaybackUI({ video_id, title, thumbnail_url: thumbnail, duration }, "playing", 0);
  })
  .catch(err => console.error("playSongFromFavorites error:", err));
}

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
const titleEl = document.getElementById("current-song-title");
const title = titleEl ? titleEl.textContent : "Unknown Title";
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
    const heartBtn = document.getElementById("current-heart-btn");
    if (heartBtn) heartBtn.textContent = "♥";
    alert(`Song '${title}' added to favorites.`);
    updateFavoritesUI_afterAdd(songObj);
  })
  .catch(err => console.error("addFavorite error:", err));
}

function removeFavorite(video_id) {
fetch(`${API.FAVORITES}/${video_id}`, { method: "DELETE" })
  .then(res => res.json())
  .then(() => {
    const heartBtn = document.getElementById("current-heart-btn");
    if (heartBtn) heartBtn.textContent = "♡";
    alert(`Song removed from favorites.`);
    removeFavoriteUI(video_id);
  })
  .catch(err => console.error("removeFavorite error:", err));
}

/* 
 NEW FUNCTION #1:
 Перевірка, чи відео вже у фаворитах, 
 щоб оновити іконку сердечка.
*/
function checkIfFavorite(video_id) {  // [ADDED FUNCTION]
fetch(API.FAVORITES)
  .then(res => res.json())
  .then(data => {
    const { favorites } = data;
    const isInFav = favorites.some(s => s.video_id === video_id);
    const heartBtn = document.getElementById("current-heart-btn");
    if (heartBtn) {
      heartBtn.textContent = isInFav ? "♥" : "♡";
    }
  })
  .catch(err => console.error("checkIfFavorite error:", err));
}

/*
 NEW FUNCTION #2:
 Викликається по кліку на іконку сердечка у playback-барі,
 щоб додати/видалити поточну пісню з фаворитів.
*/
function toggleFavoriteInPlayback() {  // [ADDED FUNCTION]
if (!window.currentVideoId) {
  console.error("No current videoId found in toggleFavoriteInPlayback");
  return;
}
toggleFavorite(window.currentVideoId);
}

/* Playback updates from socket */
function updatePlaybackUI(data) {
if (!data || !data.current_song) return;
const { video_id, title, state, position, duration } = data.current_song;

currentPlayingState = state;
currentPosition = position || 0;
currentDuration = duration || 0;

updateCurrentPlaybackUI({ video_id, title, duration }, state, currentPosition);
}

function updateCurrentPlaybackUI(songData, state, pos) {
const titleEl = document.getElementById("current-song-title");
if (titleEl) titleEl.textContent = songData.title || "Unknown";

currentDuration = songData.duration || 0;
currentPosition = pos || 0;
currentPlayingState = state;

const slider = document.getElementById("playback-progress");
if (slider) {
  slider.max = currentDuration;
  slider.value = currentPosition;
}

// Збережемо поточний video_id у глобальну змінну
window.currentVideoId = songData.video_id; // [ADDED LINE]

const heartBtn = document.getElementById("current-heart-btn");
if (heartBtn) {
  heartBtn.textContent = "♡";
}

// Перевірити, чи ця пісня вже в фаворитах:
checkIfFavorite(songData.video_id);

const playPauseBtn = document.getElementById("btn-play-pause");
if (playPauseBtn) {
  playPauseBtn.textContent = (state === "playing") ? "⏸" : "▶";
}
}

/* ========== 5. Профіль (LED, Motion) ========== */
function initProfileMenuUI() {
const ledSelect = document.getElementById("led-mode-select");
const motionToggle = document.getElementById("motion-detection-toggle");
const debouncedPrefsUpdate = debounce(updatePreferencesOnServer, 500);

// Щоб dropdown не закривався при кліку на select/checkbox
[ledSelect, motionToggle].forEach(el => {
  if (el) {
    el.addEventListener("click", evt => evt.stopPropagation());
    el.addEventListener("change", evt => evt.stopPropagation());
  }
});

if (ledSelect) {
  ledSelect.addEventListener("change", () => {
    debouncedPrefsUpdate({ led_mode: ledSelect.value });
  });
}
if (motionToggle) {
  motionToggle.addEventListener("change", () => {
    debouncedPrefsUpdate({ motion_detection: motionToggle.checked });
  });
}
}

/** Відображення dropdown при кліку по username/logo і 
*  закриття при кліку поза .profile-menu, але не при кліку на pref-item */
function initProfileDropdownToggle() {
const profileMenu = document.getElementById("profile-menu");
const profileDropdown = document.getElementById("profile-dropdown");
if (!profileMenu || !profileDropdown) return;

// Клік на сам profileMenu => тумбл .open
profileMenu.addEventListener("click", (evt) => {
  evt.stopPropagation();
  profileMenu.classList.toggle("open");
});

// Щоб клики всередині dropdown не закривали меню
profileDropdown.addEventListener("click", evt => {
  evt.stopPropagation();
});

// Клік поза меню => закриваємо
document.addEventListener("click", (evt) => {
  const isClickInside = profileMenu.contains(evt.target);
  if (!isClickInside) {
    profileMenu.classList.remove("open");
  }
});
}

/* ========== 6. Volume slider ========== */
function initVolumeUI() {
const volumeIcon = document.getElementById("volume-icon");
const volumeSliderContainer = document.getElementById("volume-slider-container");
const volumeSlider = document.getElementById("volume-slider");
const debouncedPrefsUpdate = debounce(updatePreferencesOnServer, 400);

if (!volumeIcon || !volumeSliderContainer || !volumeSlider) return;

// Клік по іконці => показати/сховати
volumeIcon.addEventListener("click", (e) => {
  e.stopPropagation();
  volumeSliderContainer.classList.toggle("show");
});

// Закриваємо, якщо клік поза контейнером
document.addEventListener("click", (evt) => {
  const isClickInside = volumeSliderContainer.contains(evt.target) || volumeIcon.contains(evt.target);
  if (!isClickInside) {
    volumeSliderContainer.classList.remove("show");
  }
});

// Зміна гучності
volumeSlider.addEventListener("input", () => {
  const val = volumeSlider.value;
  debouncedPrefsUpdate({ volume: parseFloat(val) / 100 });
});
}

/* ========== 7. Update Prefs ========== */
function updatePreferencesOnServer(updatedPrefs) {
fetch(API.PREFERENCES, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(updatedPrefs)
})
  .then(res => res.json())
  .then(data => {
    console.log("Preferences updated:", data);
  })
  .catch(err => console.error("Preferences update error:", err));
}
