
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const appCode = readFileSync(
    new URL("../frontend/js/app.js", import.meta.url),
    "utf8"
);

function createElement() {
    return {
        value: "",
        hidden: true,
        children: [],
        _text: "",

        addEventListener(event, handler) {
            this[event] = handler;
        },

        appendChild(child) {
            this.children.push(child);
        },

        set innerHTML(value) {
            this.children = [];
            this._text = "";
        },

        get textContent() {
            return this._text;
        },

        set textContent(value) {
            this._text = value;
            this.children = [];
        }
    };
}

test("frontend search recovers after a mocked HTTP 500 response", async () => {
    const elements = {
        ".hero-search": createElement(),
        "media-search": createElement(),
        "search-results": createElement(),
        "search-results-grid": createElement(),
        "genre-filter": createElement(),
        "media-type-filter": createElement(),
        "sort-filter": createElement()
    };

    elements["media-search"].value = "dark";
    elements["genre-filter"].value = "Drama";
    elements["media-type-filter"].value = "movie";

    const requests = [];

    async function mockFetch(url) {
        requests.push(url);

        if (requests.length === 1) {
            return { ok: false, status: 500 };
        }

        return {
            ok: true,
            json: async () => ({
                results: [{
                    id: "3",
                    title: "Darkest Hour",
                    type: "movie",
                    releaseYear: 2017
                }]
            })
        };
    }

    const document = {
        querySelector: (selector) => elements[selector],
        getElementById: (id) => elements[id],
        createElement
    };

    const window = {
        location: {
            hostname: "127.0.0.1",
            protocol: "http:",
            origin: "http://127.0.0.1:5500"
        }
    };

    runInNewContext(appCode, {
        window,
        document,
        fetch: mockFetch,
        URLSearchParams,
        console: { error() {} }
    });

    const form = elements[".hero-search"];
    const grid = elements["search-results-grid"];
    const section = elements["search-results"];

    const event = { preventDefault() {} };

    // First request: HTTP 500
    await form.submit(event);

    assert.equal(
        grid.textContent,
        "Unable to load search results. Please try again."
    );
    assert.equal(section.hidden, false);

    // Second request: successful API response
    await form.submit(event);

    assert.equal(requests.length, 2);
    // Verify both API requests include the correct search parameters.
    for (const requestUrl of requests) {
        const url = new URL(requestUrl);

        assert.equal(url.pathname, "/api/search");
        assert.equal(url.searchParams.get("query"), "dark");
        assert.equal(url.searchParams.get("genre"), "Drama");
        assert.equal(url.searchParams.get("media_type"), "movie");
    }
    assert.equal(grid.children.length, 1);
    assert.equal(grid.textContent, "");

    const resultCard = grid.children[0];

    assert.equal(
        resultCard.children[1].children[0].textContent,
        "Darkest Hour"
    );
});

test("latest search results remain visible when responses arrive out of order", async () => {
    const elements = {
        ".hero-search": createElement(),
        "media-search": createElement(),
        "search-results": createElement(),
        "search-results-grid": createElement(),
        "genre-filter": createElement(),
        "media-type-filter": createElement(),
        "sort-filter": createElement()
    };

    function deferred() {
        let resolve;
        const promise = new Promise((res) => {
            resolve = res;
        });
        return { promise, resolve };
    }

    const first = deferred();
    const second = deferred();
    const requests = [];

    const document = {
        querySelector: (selector) => elements[selector],
        getElementById: (id) => elements[id],
        createElement
    };

    const window = {
        location: {
            hostname: "127.0.0.1",
            protocol: "http:",
            origin: "http://127.0.0.1:5500"
        }
    };

    async function mockFetch(url) {
        requests.push(url);
        return requests.length === 1 ? first.promise : second.promise;
    }

    runInNewContext(appCode, {
        window,
        document,
        fetch: mockFetch,
        URLSearchParams,
        console: { error() {} }
    });

    const form = elements[".hero-search"];
    const grid = elements["search-results-grid"];
    const event = { preventDefault() {} };

    elements["media-search"].value = "dark";
    elements["genre-filter"].value = "Drama";
    elements["media-type-filter"].value = "tv";

    const olderSearch = form.submit(event);

    elements["media-search"].value = "dune";
    elements["genre-filter"].value = "Science Fiction";
    elements["media-type-filter"].value = "book";

    const newerSearch = form.submit(event);

    assert.equal(requests.length, 2);

    const latestRequest = new URL(requests[1]);
    assert.equal(latestRequest.searchParams.get("query"), "dune");
    assert.equal(latestRequest.searchParams.get("genre"), "Science Fiction");
    assert.equal(latestRequest.searchParams.get("media_type"), "book");

    second.resolve({
        ok: true,
        json: async () => ({
            results: [{
                id: "4",
                title: "Dune",
                type: "book",
                releaseYear: 1965
            }]
        })
    });

    await newerSearch;

    assert.equal(
        grid.children[0].children[1].children[0].textContent,
        "Dune"
    );

    first.resolve({
        ok: true,
        json: async () => ({
            results: [{
                id: "2",
                title: "Dark",
                type: "tv",
                releaseYear: 2017
            }]
        })
    });

    await olderSearch;

    assert.equal(
        grid.children[0].children[1].children[0].textContent,
        "Dune"
    );
});