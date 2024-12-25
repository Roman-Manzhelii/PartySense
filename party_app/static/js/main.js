// static/js/main.js
const API = {
    SEARCH: "/search",
    AUTOCOMPLETE: "/autocomplete",
    CONTROL: "/control_music",
};

let nextPageToken = null; // For pagination
let isLoading = false; // Prevent simultaneous API requests
let currentQuery = ""; // Track current search query
const loadedVideoIds = new Set(); // To avoid duplication

// Debounce function to limit the rate of function calls
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
}

document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("search");

    // Create autocomplete suggestions list
    const suggestionsList = createSuggestionsList(searchInput);

    // Add 'input' event listener with debounce for autocomplete
    const debouncedHandleAutocomplete = debounce(() => {
        handleAutocomplete(searchInput, suggestionsList);
    }, 300); // 300ms delay
    searchInput.addEventListener("input", debouncedHandleAutocomplete);

    // Enter key handler
    searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            initiateSearch(searchInput.value.trim());
        }
    });

    // Scroll handler to load more results when near bottom
    window.addEventListener("scroll", debounce(() => {
        if (isLoading || !nextPageToken) return;

        // Check if near bottom of page (100px buffer)
        if ((window.innerHeight + window.scrollY) >= (document.body.offsetHeight - 100)) {
            console.log("Fetching more results on scroll");
            fetchResults(currentQuery);
        }
    }, 200)); // 200ms debounce

    // Clear suggestions when clicking outside
    document.addEventListener("click", (event) => {
        clearSuggestionsOnClick(event, suggestionsList, searchInput);
    });

    // Connect to WebSocket to receive real-time statuses
    const socket = io(); // Assuming server is set up for Socket.IO
    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
    });

    socket.on('playback_update', (data) => {
        console.log('Received playback update:', data);
        // Update UI based on received data
        updatePlaybackUI(data);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket server');
    });
});

// Function to initiate search
function initiateSearch(query) {
    if (!query) {
        alert("Please enter a search query.");
        return;
    }

    const resultsGrid = document.getElementById("results-grid");
    const loadingIndicator = document.getElementById("loading");

    if (!resultsGrid || !loadingIndicator) {
        console.error("Required elements not found in DOM.");
        return;
    }

    // Clear previous results and state
    resultsGrid.innerHTML = "";
    nextPageToken = null;
    currentQuery = query;
    loadedVideoIds.clear();
    fetchResults(query);
}

// Create suggestions list element
function createSuggestionsList(searchInput) {
    const suggestionsList = document.createElement("ul");
    suggestionsList.id = "autocomplete-suggestions";
    searchInput.parentNode.insertBefore(suggestionsList, searchInput.nextSibling);
    return suggestionsList;
}

// Handle autocomplete logic
async function handleAutocomplete(searchInput, suggestionsList) {
    const query = searchInput.value.trim();
    if (query.length < 2) {
        suggestionsList.innerHTML = "";
        return;
    }

    try {
        const suggestions = await fetchSuggestions(query);
        updateSuggestionsUI(suggestions, searchInput, suggestionsList);
    } catch (error) {
        console.error("Error fetching autocomplete suggestions:", error);
    }
}

// Fetch suggestions from server
async function fetchSuggestions(query) {
    const response = await fetch(`${API.AUTOCOMPLETE}?query=${encodeURIComponent(query)}`);
    return response.ok ? response.json() : [];
}

// Update suggestions UI
function updateSuggestionsUI(suggestions, searchInput, suggestionsList) {
    suggestionsList.innerHTML = "";
    suggestions.forEach(({ title }) => {
        const li = document.createElement("li");
        li.textContent = title;
        li.classList.add("suggestion-item");
        li.addEventListener("click", () => {
            searchInput.value = title;
            suggestionsList.innerHTML = ""; // Clear suggestions
            initiateSearch(title); // Start search
        });
        suggestionsList.appendChild(li);
    });
}

// Clear suggestions when clicking outside
function clearSuggestionsOnClick(event, suggestionsList, searchInput) {
    if (!suggestionsList.contains(event.target) && event.target !== searchInput) {
        suggestionsList.innerHTML = "";
    }
}

// Fetch results and handle pagination
async function fetchResults(query) {
    if (!query || isLoading) return;

    isLoading = true;
    updateLoadingIndicator(true);

    try {
        console.log(`Fetching results for query: '${query}', pageToken: '${nextPageToken}'`);

        // Construct URL correctly to avoid passing 'null' or empty string
        let url = `${API.SEARCH}?query=${encodeURIComponent(query)}`;
        if (nextPageToken) {
            url += `&pageToken=${encodeURIComponent(nextPageToken)}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to fetch results");

        const data = await response.json();
        console.log("Received data:", data);
        updateResultsUI(data);
    } catch (error) {
        console.error("Error fetching results:", error);
    } finally {
        isLoading = false;
        updateLoadingIndicator(false);
    }
}

// Update search results in UI
function updateResultsUI(data) {
    const resultsGrid = document.getElementById("results-grid");
    nextPageToken = data.nextPageToken || null;

    console.log(`Updating results UI. Next page token: '${nextPageToken}'`);

    data.items.forEach(({ snippet, id }) => {
        if (loadedVideoIds.has(id.videoId)) {
            // If video already loaded, skip
            return;
        }

        loadedVideoIds.add(id.videoId);

        const card = document.createElement("div");
        card.className = "result-card";

        const img = document.createElement("img");
        img.src = snippet.thumbnails.medium.url;
        img.alt = snippet.title;

        const title = document.createElement("h4");
        title.textContent = snippet.title;

        card.appendChild(img);
        card.appendChild(title);

        card.addEventListener("click", () => {
            initiateSearch(snippet.title);
        });

        resultsGrid.appendChild(card);
    });

    console.log(`After update, nextPageToken is: '${nextPageToken}'`);
}

// Update loading indicator visibility
function updateLoadingIndicator(show) {
    const loadingIndicator = document.getElementById("loading");
    loadingIndicator.style.display = show ? "block" : "none";
}

// Control music playback
function controlMusic(action) {
    fetch(API.CONTROL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                console.log(`Music control response:`, data);
            } else {
                console.error(`Error:`, data.error);
            }
        })
        .catch((error) => console.error("Error controlling music:", error));
}

// Function for Search button to call initiateSearch
function searchMusic() {
    const query = document.getElementById("search").value.trim();
    initiateSearch(query);
}

// Update UI based on received playback statuses
function updatePlaybackUI(data) {
    // Example: Update playback state
    const playbackInfo = data.current_song;
    if (playbackInfo) {
        const { title, state, position } = playbackInfo;
        // Update song title
        const songTitleElement = document.getElementById("current-song-title");
        if (songTitleElement) {
            songTitleElement.textContent = title;
        }
        // Update playback state
        const playbackStateElement = document.getElementById("playback-state");
        if (playbackStateElement) {
            playbackStateElement.textContent = state;
        }
        // Update playback position
        const playbackPositionElement = document.getElementById("playback-position");
        if (playbackPositionElement) {
            playbackPositionElement.textContent = `${position} sec`;
        }
    }
}