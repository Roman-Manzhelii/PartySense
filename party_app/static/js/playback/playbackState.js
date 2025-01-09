let currentPlayingState = "pause"; 
let currentPosition = 0;
let currentDuration = 0;
let currentVideoId = null;
let playbackTimer = null;
let confirmationTimeout = null;

export function setCurrentPlayingState(state) {
  currentPlayingState = state;
}

export function getCurrentPlayingState() {
  return currentPlayingState;
}

export function setCurrentPosition(pos) {
  currentPosition = pos;
}

export function getCurrentPosition() {
  return currentPosition;
}

export function setCurrentDuration(dur) {
  currentDuration = dur;
}

export function getCurrentDuration() {
  return currentDuration;
}

export function setCurrentVideoId(id) {
  currentVideoId = id;
}

export function getCurrentVideoId() {
  return currentVideoId;
}

export function setPlaybackTimer(timer) {
  playbackTimer = timer;
}

export function getPlaybackTimer() {
  return playbackTimer;
}

export function setConfirmationTimeout(timeout) {
  confirmationTimeout = timeout;
}

export function getConfirmationTimeout() {
  return confirmationTimeout;
}
