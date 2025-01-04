import { API } from './api.js';

export function updatePreferencesOnServer(updatedPrefs) {
  fetch(API.PREFERENCES, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updatedPrefs)
  })
    .then(res => res.json())
    .then(data => {
      console.log("Settings updated:", data);
    })
    .catch(err => console.error("Settings update error:", err));
}
