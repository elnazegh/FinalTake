const searchForm = document.querySelector(".hero-search");
const searchInput = document.getElementById("media-search");
const searchResultsSection = document.getElementById("search-results");
const searchResultsGrid = document.getElementById("search-results-grid");
const genreFilter = document.getElementById("genre-filter");
const mediaTypeFilter = document.getElementById("media-type-filter");
const sortFilter = document.getElementById("sort-filter");

function renderSearchResults(results) {
    searchResultsGrid.innerHTML = "";

    if (results.length === 0) {
        searchResultsGrid.textContent = "No results found.";
        searchResultsSection.hidden = false;
        return;
    }

    results.forEach((media) => {
        const card = document.createElement("article");
        card.className = "media-card";

        const image = document.createElement("div");
        image.className = "card-image";
        image.textContent = media.type;

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

        if (!query) {
            return;
        }

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
            `http://127.0.0.1:5000/api/search?${params.toString()}`;

        try {
            const response = await fetch(url);
            const data = await response.json();

            renderSearchResults(data.results);
        } catch (error) {
            console.error("Search request failed:", error);
        }
    });
}
