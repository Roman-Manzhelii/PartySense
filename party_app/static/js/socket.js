export function setupSocket() {
  const socket = io();

  socket.on('connect', () => {
    console.log('Connected to Socket.IO server.');
  });

  socket.on('disconnect', () => {
    console.log('Disconnected from Socket.IO server.');
  });

  return socket;
}
