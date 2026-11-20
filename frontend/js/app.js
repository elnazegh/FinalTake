const API_BASE_URL =
    window.FINALTAKE_API_BASE_URL ||
    (
        ["localhost", "127.0.0.1"].includes(window.location.hostname)
            ? `${window.location.protocol}//${window.location.hostname}:5000`
            : window.location.origin
    );
const searchForm = document.querySelector(".hero-search");
const searchInput = document.getElementById("media-search");
const searchResultsSection = document.getElementById("search-results");
const searchResultsGrid = document.getElementById("search-results-grid");
const genreFilter = document.getElementById("genre-filter");
const mediaTypeFilter = document.getElementById("media-type-filter");
const sortFilter = document.getElementById("sort-filter");
let latestSearchRequestId = 0;

function renderSearchResults(results) {
    searchResultsGrid.innerHTML = "";

    if (results.length === 0) {
        searchResultsGrid.textContent = "No results found.";
        searchResultsSection.hidden = false;
        return;
    }

    results.forEach((media) => {
        const card = document.createElement("a");
        card.className = "media-card";
        card.href =
            `pages/media-details.html?id=${encodeURIComponent(media.id)}`;


const image = document.createElement("div");
image.className = "card-image";

const posterImages = {
    "The Dark Knight": "images/dark-knight.jpeg",
    "Dark": "images/dark-tv.jpeg",
    "Darkest Hour": "images/darkest-hour.jpeg",
    "Dark Souls": "images/dark-souls.jpeg"
};


const fallbackPoster = posterImages[media.title] || null;
const posterUrl = media.imageUrl || fallbackPoster;

if (posterUrl) {
    const poster = document.createElement("img");
    poster.src = posterUrl;
    poster.alt = `Poster or cover for ${media.title}`;
    poster.className = "search-poster";

    poster.onerror = () => {
        const fallbackUrl = fallbackPoster
            ? new URL(fallbackPoster, window.location.href).href
            : null;

        if (fallbackUrl && poster.src !== fallbackUrl) {
            poster.src = fallbackPoster;
        } else {
            poster.onerror = null;
            image.replaceChildren();
            image.textContent = media.type || "Image unavailable";
        }
    };

    image.appendChild(poster);
} else {
    image.textContent = media.type || "Image unavailable";
}



        const content = document.createElement("div");
        content.className = "card-content";

        const title = document.createElement("h3");
        title.textContent = media.title;

        const details = document.createElement("p");
        details.textContent = media.releaseYear
            ? `${media.type} • ${media.releaseYear}`
            : media.type;

        content.appendChild(title);
        content.appendChild(details);

        card.appendChild(image);
        card.appendChild(content);

        searchResultsGrid.appendChild(card);
    });

    searchResultsSection.hidden = false;
}

if (searchForm && searchInput) {
    searchForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const query = searchInput.value.trim();
        const genre = genreFilter.value;
        const mediaType = mediaTypeFilter.value;
        const sort = sortFilter.value;

        if (!query && !mediaType) {
            return;
        }
        const currentRequestId = ++latestSearchRequestId;

        const params = new URLSearchParams({
            query: query
        });

        if (genre) {
            params.append("genre", genre);
        }

        if (mediaType) {
            params.append("media_type", mediaType);
        }

        if (sort) {
            params.append("sort", sort);
        }

        const url =
            `${API_BASE_URL}/api/search?${params.toString()}`;

        try {
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(
                    `Search request failed with status ${response.status}`
                );
            }

            const data = await response.json();

            if (!Array.isArray(data.results)) {
                throw new Error("Search response did not contain valid results.");
            }

            if (currentRequestId !== latestSearchRequestId) {
                return;
            }

            renderSearchResults(data.results);

        } catch (error) {
            if (currentRequestId !== latestSearchRequestId) {
                return;
            }

            searchResultsGrid.innerHTML = "";
            searchResultsGrid.textContent =
                "Unable to load search results. Please try again.";

            searchResultsSection.hidden = false;

            console.error("Search request failed:", error);
        }
    });
}


document.querySelectorAll("[data-browse-type]").forEach((link) => {
    link.addEventListener("click", () => {
        searchInput.value = "";
        genreFilter.value = "";
        mediaTypeFilter.value = link.dataset.browseType;
        sortFilter.value = "";

        searchForm.requestSubmit();
    });
});
