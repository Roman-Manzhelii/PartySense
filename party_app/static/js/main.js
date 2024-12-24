const API = {
    SEARCH: "/search",
    AUTOCOMPLETE: "/autocomplete",
    CONTROL: "/control_music",
};

let nextPageToken = null; // Для пагінації
let isLoading = false; // Запобігання одночасних API-запитів
let currentQuery = ""; // Відстеження поточного пошукового запиту
const loadedVideoIds = new Set(); // Щоб уникнути дублювання

// Функція дебаунсу для обмеження частоти викликів
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
    const resultsGrid = document.getElementById("results-grid");
    const loadingIndicator = document.getElementById("loading");
    const searchInput = document.getElementById("search");

    // Створюємо список підказок автодоповнення
    const suggestionsList = createSuggestionsList(searchInput);

    // Додаємо обробник події 'input' з дебаунсом для автодоповнення
    const debouncedHandleAutocomplete = debounce(() => {
        handleAutocomplete(searchInput, suggestionsList);
    }, 1000); // 300ms затримка
    searchInput.addEventListener("input", debouncedHandleAutocomplete);

    // Обробник натискання клавіші Enter
    searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            initiateSearch(searchInput.value.trim());
        }
    });

    // Обробник прокрутки для підвантаження додаткових результатів на рівні вікна
    window.addEventListener("scroll", debounce(() => {
        if (isLoading || !nextPageToken) return;

        // Перевіряємо, чи близько до низу сторінки (100px буфер)
        if ((window.innerHeight + window.scrollY) >= (document.body.offsetHeight - 100)) {
            console.log("Виклик fetchResults при прокрутці до низу сторінки");
            fetchResults(currentQuery);
        }
    }, 200)); // 200ms дебаунс

    // Очистка підказок при кліку за межами списку
    document.addEventListener("click", (event) => {
        clearSuggestionsOnClick(event, suggestionsList, searchInput);
    });
});

// Функція для ініціалізації пошуку
function initiateSearch(query) {
    if (!query) {
        alert("Будь ласка, введіть запит для пошуку.");
        return;
    }

    const resultsGrid = document.getElementById("results-grid");
    const loadingIndicator = document.getElementById("loading");

    if (!resultsGrid || !loadingIndicator) {
        console.error("Необхідні елементи не знайдені в DOM.");
        return;
    }

    // Очищення попередніх результатів та стану
    resultsGrid.innerHTML = "";
    nextPageToken = null;
    currentQuery = query;
    loadedVideoIds.clear();
    fetchResults(query);
}

// Створюємо елемент списку для підказок
function createSuggestionsList(searchInput) {
    const suggestionsList = document.createElement("ul");
    suggestionsList.id = "autocomplete-suggestions";
    searchInput.parentNode.insertBefore(suggestionsList, searchInput.nextSibling);
    return suggestionsList;
}

// Обробляємо логіку автодоповнення
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
        console.error("Помилка при отриманні підказок автодоповнення:", error);
    }
}

// Отримуємо підказки з сервера
async function fetchSuggestions(query) {
    const response = await fetch(`${API.AUTOCOMPLETE}?query=${encodeURIComponent(query)}`);
    return response.ok ? response.json() : [];
}

// Оновлюємо UI підказок
function updateSuggestionsUI(suggestions, searchInput, suggestionsList) {
    suggestionsList.innerHTML = "";
    suggestions.forEach(({ title }) => {
        const li = document.createElement("li");
        li.textContent = title;
        li.classList.add("suggestion-item");
        li.addEventListener("click", () => {
            searchInput.value = title;
            suggestionsList.innerHTML = ""; // Очистити підказки
            initiateSearch(title); // Запустити пошук
        });
        suggestionsList.appendChild(li);
    });
}

// Очистка підказок при кліку за межами
function clearSuggestionsOnClick(event, suggestionsList, searchInput) {
    if (!suggestionsList.contains(event.target) && event.target !== searchInput) {
        suggestionsList.innerHTML = "";
    }
}

// Отримуємо результати та обробляємо пагінацію
async function fetchResults(query) {
    if (!query || isLoading) return;

    isLoading = true;
    updateLoadingIndicator(true);

    try {
        console.log(`Fetching results for query: '${query}', pageToken: '${nextPageToken}'`);

        // Конструюємо URL коректно, щоб уникнути передачі 'null' або порожнього рядка
        let url = `${API.SEARCH}?query=${encodeURIComponent(query)}`;
        if (nextPageToken) {
            url += `&pageToken=${encodeURIComponent(nextPageToken)}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error("Не вдалося отримати результати");

        const data = await response.json();
        console.log("Received data:", data);
        updateResultsUI(data);
    } catch (error) {
        console.error("Помилка при отриманні результатів:", error);
    } finally {
        isLoading = false;
        updateLoadingIndicator(false);
    }
}

// Оновлюємо результати пошуку в UI
function updateResultsUI(data) {
    const resultsGrid = document.getElementById("results-grid");
    nextPageToken = data.nextPageToken || null;

    console.log(`Updating results UI. Next page token: '${nextPageToken}'`);

    data.items.forEach(({ snippet, id }) => {
        if (loadedVideoIds.has(id.videoId)) {
            // Якщо відео вже завантажено, пропустити
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
            alert(`Video ID: ${id.videoId}`);
        });

        resultsGrid.appendChild(card);
    });

    console.log(`After update, nextPageToken is: '${nextPageToken}'`);
}

// Оновлюємо видимість індикатора завантаження
function updateLoadingIndicator(show) {
    const loadingIndicator = document.getElementById("loading");
    loadingIndicator.style.display = show ? "block" : "none";
}

// Контролюємо відтворення музики
function controlMusic(action) {
    fetch(API.CONTROL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
    })
        .then((response) => response.json())
        .then((data) => console.log(`Music control response:`, data))
        .catch((error) => console.error("Помилка при контролі музики:", error));
}

// Функція для кнопки Search, яка викликає initiateSearch
function searchMusic() {
    const query = document.getElementById("search").value.trim();
    initiateSearch(query);
}
