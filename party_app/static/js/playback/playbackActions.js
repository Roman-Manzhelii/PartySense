import { API } from "../api.js";
import { fetchCurrentPlayback } from "./initPlayback.js";
import {
  getCurrentPosition,
  setCurrentPlayingState,
  setCurrentPosition,
  getCurrentVideoId,
  setCurrentVideoId,
  getCurrentDuration,
  setCurrentDuration
} from "./playbackState.js";
import { updateCurrentPlaybackUI } from "./playbackUI.js";

export function sendControlAction(action, payload = {}) {
  const body = { action, ...payload };
  fetch(API.CONTROL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        console.error(data.error);
      }
    })
    .catch(err => console.error("Music control error:", err));
}

export function sendPauseCommand() {
  setCurrentPlayingState("pause");
  const pos = getCurrentPosition();
  updateCurrentPlaybackUI(null, "pause", pos);

  const nowTs = Date.now();
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "pause",
      position: pos,
      timestamp: nowTs
    })
  }).catch(err => {
    console.error("Error sending pause command:", err);
  });
}

export function sendSeekCommand(newPos) {
  setCurrentPosition(newPos);
  const nowTs = Date.now();
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "seek",
      position: newPos,
      timestamp: nowTs
    })
  });
}

export function playSongFromSearch(songData) {
  setCurrentPlayingState("playing");
  setCurrentPosition(0);
  setCurrentDuration(songData.duration || 0);
  setCurrentVideoId(songData.video_id);

  updateCurrentPlaybackUI(songData, "playing", 0);

  const nowTs = Date.now();
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "play",
      video_id: songData.video_id,
      title: songData.title,
      thumbnail_url: songData.thumbnail_url,
      position: 0,
      mode: "default",
      timestamp: nowTs
    })
  })
    .then(res => res.json())
    .then(() => {
      console.log("Play command sent from search.");
      // Підтягнемо оновлений стан
      fetchCurrentPlayback();
    })
    .catch(err => console.error("Error playing from search:", err));
}

export function playSongFromFavorites(songData) {
  setCurrentPlayingState("playing");
  setCurrentPosition(0);
  setCurrentDuration(songData.duration || 0);
  setCurrentVideoId(songData.video_id);

  updateCurrentPlaybackUI(songData, "playing", 0);

  const nowTs = Date.now();
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "play",
      video_id: songData.video_id,
      title: songData.title,
      thumbnail_url: songData.thumbnail_url,
      position: 0,
      mode: "default",
      timestamp: nowTs
    })
  })
    .then(res => res.json())
    .then(() => {
      console.log("Play command sent from favorites.");
      fetchCurrentPlayback();
    })
    .catch(err => console.error("Error playing from favorites:", err));
}

export function playSongFromCurrent(startPos = 0) {
  const videoId = getCurrentVideoId();
  if (!videoId) return;

  setCurrentPlayingState("playing");
  setCurrentPosition(startPos);

  updateCurrentPlaybackUI(
    {
      video_id: videoId,
      title: document.getElementById("current-song-title")?.textContent || "Unknown",
      thumbnail_url: "",
      duration: getCurrentDuration()
    },
    "playing",
    startPos
  );

  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "play",
      video_id: videoId,
      title: document.getElementById("current-song-title")?.textContent || "",
      thumbnail_url: "",
      position: startPos,
      mode: "default",
      timestamp: Date.now()
    })
  })
    .then(res => res.json())
    .then(() => {
      console.log("Play command sent from currentSong.");
      fetchCurrentPlayback();
    })
    .catch(err => {
      console.error("Error playing from current:", err);
    });
}
