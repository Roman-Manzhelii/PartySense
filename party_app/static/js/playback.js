import { API } from './api.js';
import { secondsToHMS } from './helpers.js';
import { checkIfFavorite } from './favoritesUI.js';

let currentDuration = 0;
let currentPosition = 0;
let currentPlayingState = "paused";
let playbackTimer = null;

export function setupPlaybackUI() {
  const shuffleBtn = document.getElementById("btn-shuffle");
  const prevBtn = document.getElementById("btn-prev");
  const playPauseBtn = document.getElementById("btn-play-pause");
  const nextBtn = document.getElementById("btn-next");
  const repeatBtn = document.getElementById("btn-repeat");

  shuffleBtn?.addEventListener("click", () => {
    fetch(API.PLAYBACK, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "set_mode", mode: "shuffle" })
    });
  });

  prevBtn?.addEventListener("click", () => {
    sendControlAction("previous");
  });

  playPauseBtn?.addEventListener("click", () => {
    if (currentPlayingState === "playing") {
      sendPauseCommand();
    } else {
      sendResumeCommand();
    }
  });

  nextBtn?.addEventListener("click", () => {
    sendControlAction("next");
  });

  repeatBtn?.addEventListener("click", () => {
    fetch(API.PLAYBACK, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "set_mode", mode: "repeat" })
    });
  });

  const progressSlider = document.getElementById("playback-progress");
  if (progressSlider) {
    progressSlider.addEventListener("input", (e) => {
      currentPosition = parseFloat(e.target.value);
      const progStart = document.getElementById("prog-start");
      if (progStart) {
        progStart.textContent = secondsToHMS(currentPosition);
      }
    });
    progressSlider.addEventListener("change", (e) => {
      sendSeekCommand(parseFloat(e.target.value));
    });
  }
}

export function sendControlAction(action) {
  fetch(API.CONTROL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action })
  })
    .then(res => res.json())
    .then(data => {
      if (!data.success) {
        console.error(data.error || "Music control error");
      }
    })
    .catch(err => console.error("Music control error:", err));
}

export function sendPauseCommand() {
  const nowTs = Date.now();
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "pause",
      position: currentPosition,
      timestamp: nowTs
    })
  });
}

export function sendResumeCommand() {
  const nowTs = Date.now();
  fetch(API.PLAYBACK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "resume",
      position: currentPosition,
      timestamp: nowTs
    })
  });
}

export function sendSeekCommand(newPos) {
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
      timestamp: Date.now()
    })
  })
    .then(res => res.json())
    .then(() => {
      console.log("Play command sent from search.");
    })
    .catch(err => console.error("Error playing from search:", err));
}

export function playSongFromFavorites(songData) {
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
      timestamp: Date.now()
    })
  })
    .then(res => res.json())
    .then(() => {
      console.log("Play command sent from favorites.");
    })
    .catch(err => console.error("Error playing from favorites:", err));
}

export function updatePlaybackUI(data) {
  console.log("updatePlaybackUI called with data:", data);
  if (!data || !data.current_song) return;
  const { video_id, title, state, position, duration } = data.current_song;

  console.log(`Updating playback UI: Video ID=${video_id}, Title=${title}, State=${state}, Position=${position}, Duration=${duration}`);

  currentPlayingState = state;
  currentPosition = position || 0;
  currentDuration = duration || 0;

  updateCurrentPlaybackUI({ video_id, title, duration }, state, currentPosition);

  if (state === "playing") {
    startPlaybackTimer();
  } else {
    stopPlaybackTimer();
  }
}

export function updateCurrentPlaybackUI(songData, state, pos) {
  const titleEl = document.getElementById("current-song-title");
  if (titleEl) {
    if (songData) {
      titleEl.textContent = songData.title || "Невідомо";
    } else {
      titleEl.textContent = "N/A";
    }
  }

  if (songData) {
    currentDuration = songData.duration || 0;
    currentPosition = pos || 0;
    currentPlayingState = state || "paused";
    window.currentVideoId = songData.video_id;
  } else {
    currentDuration = 0;
    currentPosition = 0;
    currentPlayingState = "paused";
    window.currentVideoId = null;
  }

  const slider = document.getElementById("playback-progress");
  if (slider) {
    slider.max = currentDuration;
    slider.value = currentPosition;
  }

  const progStart = document.getElementById("prog-start");
  if (progStart) {
    progStart.textContent = secondsToHMS(currentPosition);
  }
  const progEnd = document.getElementById("prog-end");
  if (progEnd) {
    progEnd.textContent = secondsToHMS(currentDuration);
  }

  const heartBtn = document.getElementById("current-heart-btn");
  if (heartBtn) {
    heartBtn.textContent = "♡";
  }

  if (songData) {
    checkIfFavorite(songData.video_id);
  }

  const playPauseBtn = document.getElementById("btn-play-pause");
  if (playPauseBtn) {
    playPauseBtn.textContent = (currentPlayingState === "playing") ? "⏸" : "▶";
  }
}

function startPlaybackTimer() {
  stopPlaybackTimer();
  playbackTimer = setInterval(() => {
    if (currentPlayingState === "playing") {
      currentPosition += 1;
      const slider = document.getElementById("playback-progress");
      if (slider) slider.value = currentPosition;
      const progStart = document.getElementById("prog-start");
      if (progStart) progStart.textContent = secondsToHMS(currentPosition);
      if (currentPosition >= currentDuration && currentDuration > 0) {
        stopPlaybackTimer();
      }
    }
  }, 1000);
}

function stopPlaybackTimer() {
  if (playbackTimer) {
    clearInterval(playbackTimer);
    playbackTimer = null;
  }
}

export function fetchCurrentPlayback() {
  fetch(API.CURRENT_PLAYBACK, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
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

window.addEventListener('playSongFromFavorites', (e) => {
  const songData = e.detail;
  playSongFromFavorites(songData);
});
