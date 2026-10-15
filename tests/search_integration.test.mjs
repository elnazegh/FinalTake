
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

test("search recovers after an HTTP 500 response", async () => {
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
    assert.equal(grid.children.length, 1);
    assert.equal(grid.textContent, "");

    const resultCard = grid.children[0];

    assert.equal(
        resultCard.children[1].children[0].textContent,
        "Darkest Hour"
    );
});
