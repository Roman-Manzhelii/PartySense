// Handle volume slider updates
document.addEventListener("DOMContentLoaded", () => {
    const volumeSlider = document.getElementById("volume");
    const volumeDisplay = document.getElementById("volume-display");

    if (volumeSlider && volumeDisplay) {
        volumeSlider.addEventListener("input", () => {
            volumeDisplay.textContent = `${volumeSlider.value}%`;
        });
    }

    const searchInput = document.getElementById("search");
    const suggestionsList = document.createElement("ul");
    suggestionsList.id = "autocomplete-suggestions";
    searchInput.parentNode.insertBefore(suggestionsList, searchInput.nextSibling);

    // Autocomplete logic
    searchInput.addEventListener("input", async () => {
        const query = searchInput.value.trim();
        if (query.length < 2) {
            suggestionsList.innerHTML = "";
            return;
        }

        try {
            const response = await fetch(`/autocomplete?query=${encodeURIComponent(query)}`);
            const suggestions = await response.json();

            suggestionsList.innerHTML = "";
            suggestions.forEach(({ title, video_id }) => {
                const li = document.createElement("li");
                li.textContent = title;
                li.classList.add("suggestion-item");
                li.addEventListener("click", () => {
                    searchInput.value = title; // Fill the search box
                    suggestionsList.innerHTML = ""; // Clear suggestions
                });
                suggestionsList.appendChild(li);
            });
        } catch (error) {
            console.error("Error fetching autocomplete suggestions:", error);
        }
    });

    document.addEventListener("click", (e) => {
        if (!suggestionsList.contains(e.target) && e.target !== searchInput) {
            suggestionsList.innerHTML = "";
        }
    });
});

// Search music function
function searchMusic() {
    const query = document.getElementById("search").value;
    if (!query) return;

    fetch(`/search?query=${query}`)
        .then(response => response.json())
        .then(data => {
            const resultsList = document.getElementById("results-list");
            resultsList.innerHTML = "";
            data.items.forEach(item => {
                const li = document.createElement("li");
                li.textContent = `${item.snippet.title} (ID: ${item.id.videoId})`;
                resultsList.appendChild(li);
            });
        })
        .catch(error => console.error("Error fetching search results:", error));
}

// Control music function
function controlMusic(action) {
    fetch(`/control_music`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
    })
        .then(response => response.json())
        .then(data => console.log(`Music control response:`, data))
        .catch(error => console.error("Error controlling music:", error));
}
