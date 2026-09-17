const searchForm = document.querySelector(".hero-search");
const searchInput = document.getElementById("media-search");

searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const query = searchInput.value.trim();

    if (!query) {
        return;
    }

    const url =
        `http://127.0.0.1:5000/api/search?query=${encodeURIComponent(query)}`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        console.log("Search response:", data);
    } catch (error) {
        console.error("Search request failed:", error);
    }
});
