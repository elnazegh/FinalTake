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
    title.textContent = media.title || "Untitled Media";

    const type = document.createElement("p");
    type.textContent = `Type: ${media.type || "Not available"}`;

    const genre = document.createElement("p");
    genre.textContent = `Genre: ${media.genre || "Not available"}`;

    const year = document.createElement("p");
    year.textContent = `Release Year: ${media.releaseYear ?? "Not available"}`;

    // Display media description when available.
    const description = document.createElement("p");
    description.className = "media-description";
    description.textContent = media.description
        ? media.description
        : "No description available.";

    // Display media image or a fallback.
    const imageContainer = document.createElement("div");
    imageContainer.className = "media-image-container";

    if (media.imageUrl) {
        const image = document.createElement("img");
        image.src = media.imageUrl;
        image.alt = `Poster or cover for ${media.title || "media"}`;
        image.className = "media-details-image";

        image.onerror = () => {
            imageContainer.textContent = "Image unavailable";
        };

        imageContainer.appendChild(image);
    } else {
        imageContainer.textContent = "Image unavailable";
    }

    detailsContainer.appendChild(title);
    detailsContainer.appendChild(imageContainer);
    detailsContainer.appendChild(type);
    detailsContainer.appendChild(genre);
    detailsContainer.appendChild(year);
    detailsContainer.appendChild(description);
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
if (response.status === 404) {
    detailsContainer.textContent = "Media not found.";
    return;
}

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
