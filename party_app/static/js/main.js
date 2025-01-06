import { initLottie } from "./lottie.js";
import { setupSearch } from "./search.js";
import { setupSocket } from "./socket.js";
import {
  setupPlaybackUI,
  fetchCurrentPlayback,
  setupPlaybackUpdateListener
} from "./playback/index.js";
import { initProfileMenuUI } from "./profile.js";
import { initVolumeUI } from "./volume.js";
import { initProfileDropdownToggle } from "./profileDropdown.js";
import { refreshFavoritesList, toggleFavorite } from "./favorites.js";
import { getCurrentVideoId } from "./playback/playbackState.js";

document.addEventListener("DOMContentLoaded", () => {
  initLottie();
  setupSearch();
  const socket = setupSocket();
  setupPlaybackUpdateListener(socket);
  setupPlaybackUI();
  fetchCurrentPlayback();
  initProfileMenuUI();
  initVolumeUI();
  initProfileDropdownToggle();
  refreshFavoritesList();

  const currentHeartBtn = document.getElementById("current-heart-btn");
  if (currentHeartBtn) {
    currentHeartBtn.addEventListener("click", () => {
      const videoId = getCurrentVideoId();
      if (videoId) {
        toggleFavorite(videoId);
      } else {
        console.warn("No current videoId found, can't add to favorites.");
        alert("No song is currently playing to toggle favorite.");
      }
    });
  }
});
