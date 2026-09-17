const media = [
    { id: "1", title: "The Dark Knight", type: "movie" },
    { id: "2", title: "Dark", type: "tv" },
    { id: "3", title: "Darkest Hour", type: "movie" },
    { id: "4", title: "Dune", type: "book" },
    { id: "5", title: "Dark Souls", type: "game" },
];

function searchByTitle(query) {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
    return [];
}

    return media.filter(item =>
        item.title.toLowerCase().includes(normalizedQuery)
    );
}

console.log(searchByTitle("dark"));
console.log(searchByTitle("DARK"));
console.log(searchByTitle("xyz"));
console.log(searchByTitle(""));