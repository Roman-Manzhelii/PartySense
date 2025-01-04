import { debounce } from './helpers.js';
import { updatePreferencesOnServer } from './preferences.js';

export function initProfileMenuUI() {
  const ledSelect = document.getElementById("led-mode-select");
  const motionToggle = document.getElementById("motion-detection-toggle");
  const debouncedPrefsUpdate = debounce(updatePreferencesOnServer, 500);

  [ledSelect, motionToggle].forEach(el => {
    if (el) {
      el.addEventListener("click", evt => evt.stopPropagation());
      el.addEventListener("change", evt => evt.stopPropagation());
    }
  });

  if (ledSelect) {
    ledSelect.addEventListener("change", () => {
      debouncedPrefsUpdate({ led_mode: ledSelect.value });
    });
  }
  if (motionToggle) {
    motionToggle.addEventListener("change", () => {
      debouncedPrefsUpdate({ motion_detection: motionToggle.checked });
    });
  }
}
