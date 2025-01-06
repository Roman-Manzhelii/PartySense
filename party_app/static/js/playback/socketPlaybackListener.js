import { updatePlaybackUI } from "./playbackUI.js";
import {
  getConfirmationTimeout,
  setConfirmationTimeout,
  getCurrentPlayingState
} from "./playbackState.js";
import { fetchCurrentPlayback } from "./initPlayback.js";

export function setupPlaybackUpdateListener(socket) {
  socket.on("connect", () => {
    console.log("Connected to Socket.IO server.");
  });

  socket.on("disconnect", () => {
    console.log("Disconnected from Socket.IO server.");
  });

  socket.on("playback_update", (data) => {
    console.log("Received playback_update:", data);
    if (data.current_song) {
      updatePlaybackUI(data);
      if (data.current_song.state === "pause" && getConfirmationTimeout()) {
        clearTimeout(getConfirmationTimeout());
        setConfirmationTimeout(null);
      }
    }
  });

  setInterval(() => {
    if (getCurrentPlayingState() === "playing") {
      fetchCurrentPlayback();
    }
  }, 20000);
}
