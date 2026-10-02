const API_BASE_URL =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost"
        ? `${window.location.protocol}//${window.location.hostname}:5000`
        : window.location.origin;
const params = new URLSearchParams(window.location.search);
const mediaId = params.get("id");
const detailsContainer = document.getElementById("media-details");

function renderMediaDetails(media) {
    detailsContainer.innerHTML = "";

    const title = document.createElement("h1");
    title.textContent = media.title;

    const type = document.createElement("p");
    type.textContent = `Type: ${media.type}`;

    const genre = document.createElement("p");
    genre.textContent = `Genre: ${media.genre}`;

    const year = document.createElement("p");
    year.textContent = `Release Year: ${media.releaseYear}`;

    detailsContainer.appendChild(title);
    detailsContainer.appendChild(type);
    detailsContainer.appendChild(genre);
    detailsContainer.appendChild(year);
}

async function loadMediaDetails() {
    if (!mediaId) {
        detailsContainer.textContent = "Media not found.";
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/media/${encodeURIComponent(mediaId)}`
        );

        if (!response.ok) {
            throw new Error(
                `Media request failed with status ${response.status}`
            );
        }

        const media = await response.json();
        renderMediaDetails(media);

    } catch (error) {
        detailsContainer.textContent =
            "Unable to load media details.";

        console.error("Media details request failed:", error);
    }
}

loadMediaDetails();
