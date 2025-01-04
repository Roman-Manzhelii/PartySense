import { updatePlaybackUI } from './playback.js';

export function setupSocket() {
  const socket = io();

  socket.on('connect', () => {
    console.log('Connected to Socket.IO server.');
  });

  socket.on('playback_update', (data) => {
    console.log('Received playback_update:', data);
    if (data.current_song) {
      updatePlaybackUI(data);
    }
  });

  socket.on('disconnect', () => {
    console.log('Disconnected from Socket.IO server.');
  });
}
