let currentDuration = 0;
let currentPosition = 0;
let currentPlayingState = "pause";
let confirmationTimeout = null;
let playbackTimer = null;
let currentVideoId = null;

export function getCurrentDuration() {
  return currentDuration;
}
export function setCurrentDuration(val) {
  currentDuration = val;
}

export function getCurrentPosition() {
  return currentPosition;
}
export function setCurrentPosition(val) {
  currentPosition = val;
}

export function getCurrentPlayingState() {
  return currentPlayingState;
}
export function setCurrentPlayingState(val) {
  currentPlayingState = val;
}

export function getConfirmationTimeout() {
  return confirmationTimeout;
}
export function setConfirmationTimeout(val) {
  confirmationTimeout = val;
}

export function getPlaybackTimer() {
  return playbackTimer;
}
export function setPlaybackTimer(val) {
  playbackTimer = val;
}

export function getCurrentVideoId() {
  return currentVideoId;
}
export function setCurrentVideoId(val) {
  currentVideoId = val;
}
