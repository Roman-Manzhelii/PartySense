document.addEventListener("DOMContentLoaded", async () => {
  const lottiePromise = import("./lottie.js").then(({ initLottie }) =>
    initLottie()
  );

  const otherModules = Promise.all([
    import("./search.js").then(({ setupSearch }) => setupSearch()),
    import("./socket.js").then(({ setupSocket }) => {
      const socket = setupSocket();
      import("./playback/index.js").then(({ setupPlaybackUpdateListener }) =>
        setupPlaybackUpdateListener(socket)
      );
    }),
    import("./playback/index.js").then(
      ({ setupPlaybackUI, fetchCurrentPlayback }) => {
        setupPlaybackUI();
        fetchCurrentPlayback();
      }
    ),
    import("./profile.js").then(({ initProfileMenuUI }) => initProfileMenuUI()),
    import("./volume.js").then(({ initVolumeUI }) => initVolumeUI()),
    import("./profileDropdown.js").then(({ initProfileDropdownToggle }) =>
      initProfileDropdownToggle()
    ),
    import("./favorites.js").then(
      ({ refreshFavoritesList, toggleFavorite }) => {
        refreshFavoritesList();
        const currentHeartBtn = document.getElementById("current-heart-btn");
        if (currentHeartBtn) {
          currentHeartBtn.addEventListener("click", () => {
            import("./playback/playbackState.js").then(
              ({ getCurrentVideoId }) => {
                const videoId = getCurrentVideoId();
                if (videoId) {
                  toggleFavorite(videoId);
                } else {
                  console.warn(
                    "No current videoId found, can't add to favorites."
                  );
                  alert("No song is currently playing to toggle favorite.");
                }
              }
            );
          });
        }
      }
    ),
  ]);

  await Promise.all([lottiePromise, otherModules]);
});
