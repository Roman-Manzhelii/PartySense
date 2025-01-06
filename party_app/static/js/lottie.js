export function initLottie() {
  const container = document.getElementById("lottie-container");
  const containerBottom = document.getElementById("lottie-container-bottom");

  const animations = [];

  if (container) {
    animations.push(
      lottie.loadAnimation({
        container: container,
        renderer: "svg",
        loop: true,
        autoplay: true,
        path: "/static/lottie/gradient2.json",
      })
    );
  }

  if (containerBottom) {
    animations.push(
      lottie.loadAnimation({
        container: containerBottom,
        renderer: "svg",
        loop: true,
        autoplay: true,
        path: "/static/lottie/gradient2.json",
      })
    );
  }

  return Promise.all(animations);
}
