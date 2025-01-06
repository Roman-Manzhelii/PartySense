import { updatePlaybackUI } from "./playbackUI.js";
import { API } from "../api.js";

export function fetchCurrentPlayback() {
  fetch(API.CURRENT_PLAYBACK, {
    method: "GET",
    headers: { "Content-Type": "application/json" }
  })
    .then(res => res.json())
    .then(data => {
      if (data.current_song) {
        updatePlaybackUI(data);
      } else {
        updatePlaybackUI({ current_song: null });
      }
    })
    .catch(err => console.error("Error retrieving current playback:", err));
}
