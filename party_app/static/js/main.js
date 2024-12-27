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
  
  // Висота закріпленого контейнера playback (щоб розуміти, коли пагінація)
  const pinnedPlaybackHeight = 150; // або взяти з CSS var(--playback-height)
  
  // Ініціалізація
  document.addEventListener("DOMContentLoaded", () => {
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
  
  /* ========== HELPERS ========== */
  function debounce(fn, delay) {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), delay);
    };
  }
  
  /* ========== SEARCH + AUTOCOMPLETE ========== */
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
  
    // Замість перевірки "window.innerHeight + window.scrollY >= document.body.offsetHeight",
    // перевіряємо прокручування до top playback-status
    window.addEventListener("scroll", debounce(() => {
      if (isLoading || !nextPageToken) return;
      const playbackSection = document.getElementById("playback-status");
      if (!playbackSection) return;
  
      // Відстань від верху документа до playback-status
      const topOfPlayback = playbackSection.offsetTop;
      // Поточна позиція прокрутки + видима висота
      const scrolledBottom = window.scrollY + window.innerHeight;
  
      // Якщо користувач прокрутив до початку playback
      if (scrolledBottom >= topOfPlayback) {
        fetchResults(currentQuery);
      }
    }, 200));
  
    // При кліку поза підказками — ховаємо
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
    const loadingIndicator = document.getElementById("loading");
  
    if (!resultsGrid || !loadingIndicator) {
      console.error("Missing #results-grid or #loading elements.");
      return;
    }
    resultsGrid.innerHTML = "";
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
      .then((res) => res.json())
      .then((data) => {
        nextPageToken = data.nextPageToken || null;
        updateResultsUI(data);
      })
      .catch((err) => console.error("Search error:", err))
      .finally(() => {
        isLoading = false;
        updateLoadingIndicator(false);
      });
  }
  
  function updateResultsUI(data) {
    const resultsGrid = document.getElementById("results-grid");
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
  
      // Клік => playSongFromSearch()
      card.addEventListener("click", () => {
        playSongFromSearch({
          video_id: id.videoId,
          title: snippet.title,
          thumbnail_url: snippet.thumbnails.medium.url,
          duration: 0 // При бажанні можна отримати з API
        });
      });
  
      card.appendChild(img);
      card.appendChild(titleElem);
      resultsGrid.appendChild(card);
    });
  }
  
  function updateLoadingIndicator(show) {
    const loadingIndicator = document.getElementById("loading");
    loadingIndicator.style.display = show ? "block" : "none";
  }
  
  /* ========== SOCKET.IO ========== */
  function setupSocket() {
    const socket = io();
    socket.on("connect", () => console.log("Socket connected"));
    socket.on("playback_update", (data) => {
      console.log("playback_update:", data);
      updatePlaybackUI(data);
    });
    socket.on("disconnect", () => console.log("Socket disconnected"));
  }
  
  /* ========== MUSIC PLAYBACK & FAVORITES ========== */
  function controlMusic(action) {
    fetch(API.CONTROL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action })
    })
    .then((res) => res.json())
    .then((data) => {
      if (!data.success) {
        console.error(data.error || "Music control error");
      }
    })
    .catch((err) => console.error("controlMusic error:", err));
  }
  
  // При кліку на результат пошуку
  function playSongFromSearch(songData) {
    // Надсилаємо запит на відтворення + додамо логіку "логування історії"
    fetch(API.PLAYBACK, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "play",
        video_id: songData.video_id,
        position: 0,
        mode: "default",
        // thumbnail, title => потрібні для історії
        thumbnail_url: songData.thumbnail_url,
        title: songData.title
      })
    })
    .then((res) => res.json())
    .then((resp) => {
      console.log("Play from search:", resp);
      updateCurrentPlaybackUI(songData, "playing", 0);
    })
    .catch((err) => console.error("playSongFromSearch error:", err));
  }
  
  // При кліку на "Play" у Favorites
  function playSongFromFavorites(btn) {
    const li = btn.closest(".favorite-item");
    if (!li) return;
  
    const video_id = li.dataset.videoId;
    const title = li.dataset.title;
    const thumbnail = li.dataset.thumbnail;
    const duration = li.dataset.duration || 0;
  
    fetch(API.PLAYBACK, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "play",
        video_id,
        position: 0,
        mode: "default",
        thumbnail_url: thumbnail,
        title: title
      })
    })
    .then((res) => res.json())
    .then((data) => {
      console.log("Playing favorite:", data);
      updateCurrentPlaybackUI({ video_id, title, thumbnail_url: thumbnail, duration }, "playing", 0);
    })
    .catch((err) => console.error("playSongFromFavorites error:", err));
  }
  
  // Локальне оновлення current playback
  function updateCurrentPlaybackUI(songData, state, position) {
    document.getElementById("current-song-title").textContent = songData.title || "Unknown";
    document.getElementById("playback-state").textContent = state || "Stopped";
    document.getElementById("playback-position").textContent = `${position} sec`;
  
    window.__currentPlaybackId = songData.video_id || "";
    checkIfFavorite(songData.video_id);
  }
  
  // Перевірка чи в Fav
  function checkIfFavorite(video_id) {
    if (!video_id) return;
    fetch(API.FAVORITES)
      .then((res) => res.json())
      .then((data) => {
        const { favorites } = data;
        const isFav = favorites.some((s) => s.video_id === video_id);
        const heartBtn = document.getElementById("current-heart-btn");
        if (heartBtn) {
          heartBtn.textContent = isFav ? "♥" : "♡";
        }
      })
      .catch((err) => console.error("checkIfFavorite error:", err));
  }
  
  function toggleFavoriteInPlayback() {
    const video_id = window.__currentPlaybackId;
    if (!video_id) return;
    toggleFavorite(video_id);
  }
  
  // Якщо немає -> додати, інакше видалити
  function toggleFavorite(video_id) {
    fetch(API.FAVORITES)
      .then((res) => res.json())
      .then((data) => {
        const { favorites } = data;
        const isInFav = favorites.some((s) => s.video_id === video_id);
        if (isInFav) removeFavorite(video_id);
        else addFavorite(video_id);
      })
      .catch((err) => console.error("toggleFavorite fetch error:", err));
  }
  
  // Додаємо в Favorites
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
    .then((res) => res.json())
    .then(() => {
      document.getElementById("current-heart-btn").textContent = "♥";
      alert(`Song '${title}' added to favorites.`);
    })
    .catch((err) => console.error("addFavorite error:", err));
  }
  
  // Видаляємо з Favorites
  function removeFavorite(video_id) {
    fetch(`${API.FAVORITES}/${video_id}`, { method: "DELETE" })
      .then((res) => res.json())
      .then(() => {
        document.getElementById("current-heart-btn").textContent = "♡";
        alert(`Song removed from favorites.`);
        // Видаляємо з DOM (якщо існує)
        const li = document.querySelector(`.favorite-item[data-video-id="${video_id}"]`);
        if (li) li.remove();
      })
      .catch((err) => console.error("removeFavorite error:", err));
  }
  
  // Коли надходить playback_update через SocketIO
  function updatePlaybackUI(data) {
    if (!data || !data.current_song) return;
    const { video_id, title, state, position } = data.current_song;
    document.getElementById("current-song-title").textContent = title || "N/A";
    document.getElementById("playback-state").textContent = state || "Stopped";
    document.getElementById("playback-position").textContent = `${position} sec`;
  
    window.__currentPlaybackId = video_id || "";
    checkIfFavorite(video_id);
  }
  