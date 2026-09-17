const searchEndpoint = "/api/search";
const sampleResults = [
    {
        id: "1",
        title: "The Dark Knight",
        type: "movie",
        imageUrl: null,
        releaseYear: 2008
    },
    {
        id: "2",
        title: "Dark Souls",
        type: "game",
        imageUrl: null,
        releaseYear: 2011
    }
];

function buildSearchUrl(query) {
    const normalizedQuery = query.trim();

    if (!normalizedQuery) {
        return null;
    }

    return `${searchEndpoint}?query=${encodeURIComponent(normalizedQuery)}`;
}

console.log(buildSearchUrl("dark"));
console.log(buildSearchUrl("Dark Souls"));
console.log(buildSearchUrl(""));

function createSearchResponse(results) {
    return {
        results
    };
}

console.log(createSearchResponse(sampleResults));
console.log(createSearchResponse([]));

function createErrorResponse(message) {
    return {
        error: message
    };
}

console.log(createErrorResponse("Unable to complete search."));