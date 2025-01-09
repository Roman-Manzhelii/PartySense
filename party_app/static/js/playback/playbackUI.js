import {
  setCurrentPlayingState,
  getCurrentPlayingState,
  getCurrentDuration,
  setCurrentDuration,
  getCurrentPosition,
  setCurrentPosition,
  setCurrentVideoId,
  getPlaybackTimer,
  getCurrentVideoId
} from "./playbackState.js";
import { checkIfFavorite } from "../favoritesUI.js";
import { secondsToHMS } from "../helpers.js";
import { startPlaybackTimer, stopPlaybackTimer } from "./playbackTimer.js";

function getPlayPauseBtn() {
  return document.getElementById("btn-play-pause");
}

export function showLoadingState() {
  const btn = getPlayPauseBtn();
  if (!btn) return;
  const orig = btn.textContent || "▶";
  btn.setAttribute("data-orig-text", orig);
  btn.textContent = "";
  btn.disabled = true;
  btn.classList.add("loading-spinner");
}

export function hideLoadingState() {
  const btn = getPlayPauseBtn();
  if (!btn) return;
  btn.classList.remove("loading-spinner");
  btn.disabled = false;
  const orig = btn.getAttribute("data-orig-text") || "▶";
  btn.textContent = orig;
  btn.removeAttribute("data-orig-text");
  if (getCurrentPlayingState() === "playing" && !getPlaybackTimer()) {
    startPlaybackTimer();
  }
}

export function updatePlaybackUI(data) {
  console.log("updatePlaybackUI called with data:", data);
  if (!data || !data.current_song) return;
  const incomingSong = data.current_song;
  const currentLocalId = getCurrentVideoId();
  const { video_id, title, state, position, duration } = incomingSong;
  console.log(
    `Updating playback UI with [${video_id}, ${title}, ${state}, pos=${position}, dur=${duration}]`
  );

  let finalPos = position || 0;
  const localPos = getCurrentPosition();
  const localState = getCurrentPlayingState();

  if (localState === "playing" && localPos > finalPos) {
    console.log(`[updatePlaybackUI] localPos ${localPos} > serverPos ${finalPos}, keep local pos`);
    finalPos = localPos;
  } else if (finalPos > localPos) {
    console.log(`[updatePlaybackUI] serverPos ${finalPos} > localPos ${localPos}, use serverPos`);
  }

  // Скидання позиції в 0 при зміні пісні
  if (video_id !== currentLocalId) {
    setCurrentVideoId(video_id);
    setCurrentPosition(0);
    finalPos = 0;
  }

  setCurrentPlayingState(state);
  setCurrentPosition(finalPos);
  setCurrentDuration(duration || 0);

  const skipTitleUpdate = incomingSong.state === "pause" && currentLocalId && video_id !== currentLocalId;
  updateCurrentPlaybackUI(
    skipTitleUpdate ? null : { video_id, title, duration },
    state,
    skipTitleUpdate ? 0 : finalPos
  );

  if (state === "playing") {
    if (!getPlaybackTimer()) {
      console.log("[updatePlaybackUI] => startPlaybackTimer()");
      startPlaybackTimer();
    }
  } else {
    console.log("[updatePlaybackUI] state != playing => stopPlaybackTimer()");
    stopPlaybackTimer();
  }
}

export function updateCurrentPlaybackUI(songData, state, pos) {
  const titleEl = document.getElementById("current-song-title");
  if (!songData && state === "pause") {
    // Якщо немає даних про трек і він на паузі — залишаємо попереднє відображення
  } else if (!songData) {
    if (titleEl) titleEl.textContent = "N/A";
  } else {
    if (titleEl) {
      titleEl.textContent = songData.title || "Unknown";
    }
    setCurrentVideoId(songData.video_id);
    setCurrentDuration(songData.duration || 0);
    const heartBtn = document.getElementById("current-heart-btn");
    if (heartBtn && songData.video_id) {
      checkIfFavorite(songData.video_id);
    }
  }
  setCurrentPlayingState(state);
  setCurrentPosition(pos || 0);
  const slider = document.getElementById("playback-progress");
  if (slider) {
    slider.max = getCurrentDuration();
    slider.value = getCurrentPosition();
  }
  const progStart = document.getElementById("prog-start");
  if (progStart) {
    progStart.textContent = secondsToHMS(getCurrentPosition());
  }
  const progEnd = document.getElementById("prog-end");
  if (progEnd) {
    progEnd.textContent = secondsToHMS(getCurrentDuration());
  }
  const playPauseBtn = document.getElementById("btn-play-pause");
  if (playPauseBtn) {
    playPauseBtn.textContent = (state === "playing") ? "⏸" : "▶";
  }
}

export function updatePositionOnBackend(position) {
  console.log("[updatePositionOnBackend] sending update_position with pos =", position);
  const nowTs = Date.now();
  fetch("/api/playback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "update_position",
      position,
      timestamp: nowTs
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data && data.error) {
        console.error("Failed to update position:", data.error);
      } else {
        console.log("[updatePositionOnBackend] success, server responded:", data);
      }
    })
    .catch(err => {
      console.error("Error updating position on backend:", err);
    });
}
