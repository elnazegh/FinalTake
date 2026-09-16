const allowedTypes = ["movie", "tv", "book", "game"];

function createMediaSearchResult(id, title, type, imageUrl = null, releaseYear = null) {
    if (!id || !title || !type) {
        return null;
    }

    if (!allowedTypes.includes(type)) {
        return null;
    }

    return {
        id,
        title,
        type,
        imageUrl,
        releaseYear
    };
}
console.log(createMediaSearchResult("1", "Interstellar", "movie"));
console.log(createMediaSearchResult("2", "Dune", "book"));
console.log(createMediaSearchResult("3", "Dark Souls", "game"));
console.log(createMediaSearchResult("4", "Breaking Bad", "tv"));
console.log(createMediaSearchResult("5", "Unknown", "podcast"));
console.log(createMediaSearchResult("6", "", "movie"));
console.log(
    createMediaSearchResult(
        "7",
        "Interstellar",
        "movie",
        "https://example.com/interstellar.jpg",
        2014
    )
);