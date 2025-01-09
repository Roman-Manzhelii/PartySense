import {
  getCurrentPosition,
  setCurrentPosition,
  getCurrentPlayingState,
  setCurrentPlayingState,
  getCurrentDuration,
  getPlaybackTimer,
  setPlaybackTimer
} from "./playbackState.js";
import { secondsToHMS } from "../helpers.js";
import {
  updateCurrentPlaybackUI,
  updatePositionOnBackend
} from "./playbackUI.js";

let positionUpdateIntervalId = null;

export function startPlaybackTimer() {
  if (getPlaybackTimer()) return;
  const mainTimer = setInterval(() => {
    const st = getCurrentPlayingState();
    if (st === "playing") {
      const newPos = getCurrentPosition() + 1;
      setCurrentPosition(newPos);
      const slider = document.getElementById("playback-progress");
      if (slider) slider.value = newPos;
      const progStart = document.getElementById("prog-start");
      if (progStart) {
        progStart.textContent = secondsToHMS(newPos);
      }
      if (newPos >= getCurrentDuration() && getCurrentDuration() > 0) {
        stopPlaybackTimer();
        setCurrentPlayingState("pause");
        const playPauseBtn = document.getElementById("btn-play-pause");
        if (playPauseBtn) playPauseBtn.textContent = "▶";
        updateCurrentPlaybackUI(null, "pause", getCurrentDuration());
        fetch("/api/playback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "pause",
            position: getCurrentDuration(),
            timestamp: Date.now()
          })
        });
      }
    }
  }, 1000);
  setPlaybackTimer(mainTimer);
  positionUpdateIntervalId = setInterval(() => {
    const st = getCurrentPlayingState();
    if (st === "playing") {
      updatePositionOnBackend(getCurrentPosition());
    }
  }, 20000);
}

export function stopPlaybackTimer() {
  const mainTimer = getPlaybackTimer();
  if (mainTimer) {
    clearInterval(mainTimer);
    setPlaybackTimer(null);
  }
  if (positionUpdateIntervalId) {
    clearInterval(positionUpdateIntervalId);
    positionUpdateIntervalId = null;
  }
}
