const API_BASE_URL =
    window.FINALTAKE_API_BASE_URL ||
    (
        ["localhost", "127.0.0.1"].includes(window.location.hostname)
            ? `${window.location.protocol}//${window.location.hostname}:5000`
            : window.location.origin
    );
const params = new URLSearchParams(window.location.search);
const mediaId = params.get("id");
const detailsContainer = document.getElementById("media-details");
const editMediaLink = document.getElementById("edit-media-link");
const deleteMediaButton = document.getElementById("delete-media-button");
const deleteMediaMessage = document.getElementById("delete-media-message");
let mediaTitle = "";

async function showEditLink() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/media/permissions`, {
            credentials: "include"
        });
        if (!response.ok) {
            throw new Error(`Permission check failed (${response.status})`);
        }
        const permissions = await response.json();
        if (permissions.canManageMedia === true) {
            editMediaLink.href = `edit-media.html?id=${encodeURIComponent(mediaId)}`;
            editMediaLink.hidden = false;
            deleteMediaButton.hidden = false;
        }
    } catch (error) {
        console.error("Unable to check media permissions:", error);
    }
}

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


const fallbackPoster =
    String(mediaId) === "1"
        ? "../images/dark-knight.jpeg"
        : null;

const posterUrl = media.imageUrl || fallbackPoster;

if (posterUrl) {
    const image = document.createElement("img");
    image.src = posterUrl;
    image.alt = `Poster or cover for ${media.title || "media"}`;
    image.className = "media-details-image";

    image.onerror = () => {
        const fallbackUrl = fallbackPoster
            ? new URL(fallbackPoster, window.location.href).href
            : null;

        if (fallbackUrl && image.src !== fallbackUrl) {
            image.src = fallbackPoster;
        } else {
            image.onerror = null;
            image.remove();
            imageContainer.textContent = "Image unavailable";
        }
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
        mediaTitle = media.title;
        renderMediaDetails(media);
        await showEditLink();

    } catch (error) {
        detailsContainer.textContent =
            "Unable to load media details.";

        console.error("Media details request failed:", error);
    }
}

deleteMediaButton.addEventListener("click", async () => {
    if (deleteMediaButton.disabled) return;
    if (!window.confirm(`Delete "${mediaTitle}" from the catalog?`)) return;

    deleteMediaButton.disabled = true;
    deleteMediaMessage.hidden = true;
    try {
        const response = await fetch(
            `${API_BASE_URL}/api/media/${encodeURIComponent(mediaId)}`,
            { method: "DELETE", credentials: "include" }
        );
        if (response.status !== 200) {
            if (response.status === 401 || response.status === 403) {
                deleteMediaMessage.textContent = "You are not authorized to delete this media.";
            } else if (response.status === 404) {
                deleteMediaMessage.textContent = "Media not found or already deleted.";
            } else {
                deleteMediaMessage.textContent = "Unable to delete media. Please try again.";
            }
            deleteMediaMessage.hidden = false;
            return;
        }
        detailsContainer.hidden = true;
        editMediaLink.hidden = true;
        deleteMediaButton.hidden = true;
        document.getElementById("reviews-section").hidden = true;
        deleteMediaMessage.textContent =
            "Media deleted successfully. Use Back to Search to return to the catalog.";
        deleteMediaMessage.hidden = false;
    } catch (error) {
        console.error("Media deletion failed:", error);
        deleteMediaMessage.textContent = "Unable to delete media. Please try again.";
        deleteMediaMessage.hidden = false;
    } finally {
        deleteMediaButton.disabled = false;
    }
});

loadMediaDetails();
