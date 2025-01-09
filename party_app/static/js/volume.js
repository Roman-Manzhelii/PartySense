import { debounce } from './helpers.js';
import { updatePreferencesOnServer } from './preferences.js';

export function initVolumeUI() {
  const volumeIcon = document.getElementById("volume-icon");
  const volumeSliderContainer = document.getElementById("volume-slider-container");
  const volumeSlider = document.getElementById("volume-slider");
  const debouncedPrefsUpdate = debounce(updatePreferencesOnServer, 400);

  if (!volumeIcon || !volumeSliderContainer || !volumeSlider) return;

  if (volumeSlider.value === "0") {
    volumeIcon.textContent = "🔇";
  } else {
    volumeIcon.textContent = "🔊";
  }

  volumeIcon.addEventListener("click", (e) => {
    e.stopPropagation();
    volumeSliderContainer.classList.toggle("show");
  });

  document.addEventListener("click", (evt) => {
    const isClickInside = volumeSliderContainer.contains(evt.target) || volumeIcon.contains(evt.target);
    if (!isClickInside) {
      volumeSliderContainer.classList.remove("show");
    }
  });

  volumeSlider.addEventListener("input", () => {
    const val = volumeSlider.value;
    debouncedPrefsUpdate({ volume: parseFloat(val) / 100 });
    if (val === "0") {
      volumeIcon.textContent = "🔇";
    } else {
      volumeIcon.textContent = "🔊";
    }
  });
}
