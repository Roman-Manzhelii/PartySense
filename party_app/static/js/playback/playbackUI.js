import {
  setCurrentPlayingState,
  getCurrentPlayingState,
  getCurrentDuration,
  setCurrentDuration,
  getCurrentPosition,
  setCurrentPosition,
  setCurrentVideoId,
  getPlaybackTimer
} from "./playbackState.js";
import { checkIfFavorite } from "../favoritesUI.js";
import { secondsToHMS } from "../helpers.js";
import { startPlaybackTimer, stopPlaybackTimer } from "./playbackTimer.js";

export function updatePlaybackUI(data) {
  console.log("updatePlaybackUI called with data:", data);
  if (!data || !data.current_song) return;

  const { video_id, title, state, position, duration } = data.current_song;
  console.log(
    `Updating playback UI with [${video_id}, ${title}, ${state}, pos=${position}, dur=${duration}]`
  );

  const localPos = getCurrentPosition();
  const localState = getCurrentPlayingState();
  let finalPos = position || 0;

  // Логіка “не відкочуватися назад”
  if (localState === "playing" && localPos > finalPos) {
    console.log(`[updatePlaybackUI] localPos ${localPos} > serverPos ${finalPos}, keep local pos`);
    finalPos = localPos;
  } else if (finalPos > localPos) {
    console.log(`[updatePlaybackUI] serverPos ${finalPos} > localPos ${localPos}, use serverPos`);
  }

  setCurrentPlayingState(state);
  setCurrentPosition(finalPos);
  setCurrentDuration(duration || 0);

  updateCurrentPlaybackUI(
    { video_id, title, duration },
    state,
    finalPos
  );

  // ====== ОНОВЛЕНА ЛОГІКА ======
  if (state === "playing") {
    // якщо або localState != playing, або таймер не запущений => треба start
    // інакше, якщо Timer уже є, все гаразд
    if (localState !== "playing" || !getPlaybackTimer()) {
      console.log("[updatePlaybackUI] => startPlaybackTimer() (force start if no timer)");
      startPlaybackTimer();
    } else {
      console.log("[updatePlaybackUI] already playing and timer is running => do nothing");
    }
  } else {
    console.log("[updatePlaybackUI] state != playing => stopPlaybackTimer()");
    stopPlaybackTimer();
  }
}

export function updateCurrentPlaybackUI(songData, state, pos) {
  const titleEl = document.getElementById("current-song-title");
  if (state === "pause" && !songData) {
    // skip
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

/**
 * Called explicitly from the 20s interval in playbackTimer.js
 */
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
