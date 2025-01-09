import { API } from "../api.js";
import { fetchCurrentPlayback } from "./initPlayback.js";
import {
  getCurrentPosition,
  getCurrentPlayingState,
  setCurrentPlayingState,
  setCurrentPosition,
  getCurrentVideoId,
  setCurrentVideoId,
  getCurrentDuration,
  setCurrentDuration
} from "./playbackState.js";
import {
  updateCurrentPlaybackUI,
  showLoadingState,
  hideLoadingState
} from "./playbackUI.js";

function pauseIfPlaying() {
  if (getCurrentPlayingState() !== "playing") return Promise.resolve();
  showLoadingState();
  const pos = getCurrentPosition();
  setCurrentPlayingState("pause");
  updateCurrentPlaybackUI(null, "pause", pos);
  const nowTs = Date.now();
  return fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "pause",
      position: pos,
      timestamp: nowTs
    })
  }).then(() => {
    hideLoadingState();
    return fetchCurrentPlayback();
  });
}

export function sendControlAction(action, payload = {}) {
  const body = { action, ...payload };
  fetch(API.CONTROL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

export function sendPauseCommand() {
  showLoadingState();
  const pos = getCurrentPosition();
  setCurrentPlayingState("pause");
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
  }).then(() => {
    hideLoadingState();
    fetchCurrentPlayback();
  });
}

export function sendSeekCommand(newPos) {
  const nowTs = Date.now();
  setCurrentPosition(newPos);
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "seek",
      position: newPos,
      timestamp: nowTs
    })
  }).then(() => {
    fetchCurrentPlayback();
  });
}

export function playSongFromSearch(songData) {
  pauseIfPlaying().then(() => {
    showLoadingState();
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
    }).then(() => {
      hideLoadingState();
      fetchCurrentPlayback();
    });
  });
}

export function playSongFromFavorites(songData) {
  pauseIfPlaying().then(() => {
    showLoadingState();
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
    }).then(() => {
      hideLoadingState();
      fetchCurrentPlayback();
    });
  });
}

export function playSongFromCurrent(startPos = 0) {
  pauseIfPlaying().then(() => {
    showLoadingState();
    const videoId = getCurrentVideoId();
    if (!videoId) {
      hideLoadingState();
      return;
    }
    setCurrentPlayingState("playing");
    setCurrentPosition(startPos);
    updateCurrentPlaybackUI({
      video_id: videoId,
      title: document.getElementById("current-song-title")?.textContent || "Unknown",
      thumbnail_url: "",
      duration: getCurrentDuration()
    }, "playing", startPos);
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
    }).then(() => {
      hideLoadingState();
      fetchCurrentPlayback();
    });
  });
}
