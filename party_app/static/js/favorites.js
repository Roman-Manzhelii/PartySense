import { API } from './api.js';
import { playSongFromFavorites } from './playback/playbackActions.js';

export function toggleFavorite(video_id) {
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
    .catch(err => console.error("Error retrieving favorites:", err));
}

export function addFavorite(video_id) {
  fetch(API.FAVORITES, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id })
  })
    .then(res => res.json())
    .then(() => {
      const heartBtn = document.getElementById("current-heart-btn");
      if (heartBtn) heartBtn.textContent = "♥";
      alert(`Song added to favorites.`);
      refreshFavoritesList();
    })
    .catch(err => console.error("Error adding to favorites:", err));
}

export function removeFavorite(video_id) {
  fetch(`${API.FAVORITES}/${video_id}`, { method: "DELETE" })
    .then(res => res.json())
    .then(() => {
      const heartBtn = document.getElementById("current-heart-btn");
      if (heartBtn) heartBtn.textContent = "♡";
      alert(`Song removed from favorites.`);
      refreshFavoritesList();
    })
    .catch(err => console.error("Error deleting from favorites:", err));
}

export function refreshFavoritesList() {
  fetch(API.FAVORITES)
    .then(r => r.json())
    .then(data => {
      const favorites = data.favorites || [];
      const favList = document.getElementById("favorites-list");
      if (!favList) return;
      favList.innerHTML = "";
      favorites.forEach(song => {
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
        playBtn.addEventListener("click", () => {
          playSongFromFavorites({
            video_id: song.video_id,
            title: song.title,
            thumbnail_url: song.thumbnail_url,
            duration: song.duration
          });
        });

        li.appendChild(spanTitle);
        li.appendChild(heartBtn);
        li.appendChild(playBtn);
        favList.appendChild(li);
      });
    })
    .catch(err => console.error("Error updating favorites list:", err));
}