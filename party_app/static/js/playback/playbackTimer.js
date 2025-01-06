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
  // Якщо вже запущено — не робимо вдруге
  if (getPlaybackTimer()) {
    console.log("[startPlaybackTimer] Timer already running. Skip re-init.");
    return;
  }

  console.log("[startPlaybackTimer] Called.");

  // Основний 1-секундний таймер
  const mainTimer = setInterval(() => {
    const st = getCurrentPlayingState();
    if (st === "playing") {
      const newPos = getCurrentPosition() + 1;
      setCurrentPosition(newPos);

      console.log(`[TimerTick] state=${st}, newPos=${newPos}`);

      // Оновлюємо UI
      const slider = document.getElementById("playback-progress");
      if (slider) slider.value = newPos;

      const progStart = document.getElementById("prog-start");
      if (progStart) {
        progStart.textContent = secondsToHMS(newPos);
      }

      // Якщо досягли кінця
      if (newPos >= getCurrentDuration() && getCurrentDuration() > 0) {
        console.log("[TimerTick] Reached end => pause");
        stopPlaybackTimer();
        setCurrentPlayingState("pause");

        const playPauseBtn = document.getElementById("btn-play-pause");
        if (playPauseBtn) {
          playPauseBtn.textContent = "▶";
        }
        updateCurrentPlaybackUI(null, "pause", getCurrentDuration());

        // Відправимо "pause"
        fetch("/api/playback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "pause",
            position: getCurrentDuration(),
            timestamp: Date.now()
          })
        }).catch(err => console.error("Error sending final pause command:", err));
      }
    }
  }, 1000);

  setPlaybackTimer(mainTimer);

  // Додатковий інтервал — раз на 20s
  positionUpdateIntervalId = setInterval(() => {
    const st = getCurrentPlayingState();
    if (st === "playing") {
      const pos = getCurrentPosition();
      console.log(`[20s Interval] state=playing => update_position pos=${pos}`);
      updatePositionOnBackend(pos);
    } else {
      console.log("[20s Interval] state != playing => skip");
    }
  }, 20000);
}

export function stopPlaybackTimer() {
  console.log("[stopPlaybackTimer] Called.");
  const mainTimer = getPlaybackTimer();
  if (mainTimer) {
    console.log("[stopPlaybackTimer] Clearing mainTimer (1s).");
    clearInterval(mainTimer);
    setPlaybackTimer(null);
  }
  if (positionUpdateIntervalId) {
    console.log("[stopPlaybackTimer] Clearing positionUpdateInterval (20s).");
    clearInterval(positionUpdateIntervalId);
    positionUpdateIntervalId = null;
  }
}
