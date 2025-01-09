import {
  sendPauseCommand,
  playSongFromCurrent,
  sendControlAction,
  sendSeekCommand
} from "./playbackActions.js";
import {
  getCurrentPlayingState,
  getCurrentPosition,
  getCurrentDuration
} from "./playbackState.js";
import { secondsToHMS } from "../helpers.js";

export function setupPlaybackUI() {
  const playPauseBtn = document.getElementById("btn-play-pause");
  const shuffleBtn = document.getElementById("btn-shuffle");
  const prevBtn = document.getElementById("btn-prev");
  const nextBtn = document.getElementById("btn-next");
  const repeatBtn = document.getElementById("btn-repeat");

  shuffleBtn?.addEventListener("click", () => {
    sendControlAction("set_mode", { mode: "shuffle" });
  });

  prevBtn?.addEventListener("click", () => {
    sendControlAction("previous");
  });

  playPauseBtn?.addEventListener("click", () => {
    const st = getCurrentPlayingState();
    if (st === "playing") {
      sendPauseCommand();
    } else {
      const curPos = getCurrentPosition();
      if (curPos >= getCurrentDuration()) {
        playSongFromCurrent(0);
      } else {
        playSongFromCurrent(curPos);
      }
    }
  });

  nextBtn?.addEventListener("click", () => {
    sendControlAction("next");
  });

  repeatBtn?.addEventListener("click", () => {
    sendControlAction("set_mode", { mode: "repeat" });
  });

  const progressSlider = document.getElementById("playback-progress");
  if (progressSlider) {
    progressSlider.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      const progStart = document.getElementById("prog-start");
      if (progStart) {
        progStart.textContent = secondsToHMS(val);
      }
    });
    progressSlider.addEventListener("change", (e) => {
      const newVal = parseFloat(e.target.value);
      sendSeekCommand(newVal);
    });
  }
}
