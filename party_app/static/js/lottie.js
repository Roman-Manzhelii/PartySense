export function initLottie() {
    const container = document.getElementById("lottie-container");
    if (container) {
      lottie.loadAnimation({
        container: container,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: '/static/lottie/gradient2.json'
      });
    }
  
    const containerBottom = document.getElementById("lottie-container-bottom");
    if (containerBottom) {
      lottie.loadAnimation({
        container: containerBottom,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: '/static/lottie/gradient2.json'
      });
    }
  }
  