import { API } from './api.js';

export function checkIfFavorite(video_id) {
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
    .catch(err => console.error("Error checking favorite song:", err));
}