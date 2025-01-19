import { updatePlaybackUI } from "./playbackUI.js";
import { getConfirmationTimeout, setConfirmationTimeout } from "./playbackState.js";
import { fetchCurrentPlayback } from "./initPlayback.js";

export function setupPlaybackUpdateListener(socket) {
  socket.on("connect", () => {});
  socket.on("disconnect", () => {});
  socket.on("playback_update", (data) => {
    updatePlaybackUI(data);
    if (data.current_song && data.current_song.state === "pause" && getConfirmationTimeout()) {
      clearTimeout(getConfirmationTimeout());
      setConfirmationTimeout(null);
    }
  });
  
  setInterval(() => {
    const btn = document.getElementById("btn-play-pause");
    if (btn && btn.classList.contains("loading-spinner")) {
      console.log("Спінер активний, пропуск fetchCurrentPlayback");
      return;
    }
    fetchCurrentPlayback();
  }, 20000);
}
