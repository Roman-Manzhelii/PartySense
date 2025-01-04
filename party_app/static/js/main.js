import { initLottie } from './lottie.js';
import { setupSearch } from './search.js';
import { setupSocket } from './socket.js';
import { setupPlaybackUI, fetchCurrentPlayback } from './playback.js';
import { initProfileMenuUI } from './profile.js';
import { initVolumeUI } from './volume.js';
import { initProfileDropdownToggle } from './profileDropdown.js';
import { refreshFavoritesList, toggleFavorite } from './favorites.js';

document.addEventListener("DOMContentLoaded", () => {
  initLottie();
  setupSearch();
  setupSocket();
  setupPlaybackUI();
  initProfileMenuUI();
  initVolumeUI();
  initProfileDropdownToggle();
  fetchCurrentPlayback();
  refreshFavoritesList();
  
  window.toggleFavoriteInPlayback = () => {
    if (window.currentVideoId) {
      toggleFavorite(window.currentVideoId);
    } else {
      console.error("No currentVideoId available for toggling favorite.");
      alert("No song is currently playing to toggle favorite.");
    }
  };
  
  window.toggleFavorite = (video_id) => {
    toggleFavorite(video_id);
  };
});