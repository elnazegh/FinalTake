
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const script = readFileSync(
    new URL("../frontend/js/media-details.js", import.meta.url),
    "utf8"
);

// Run the actual frontend JavaScript with simulated API responses.
async function runMediaDetails(search, response, apiBaseUrl) {
    const container = {
        textContent: "",
        children: [],

        set innerHTML(value) {
            if (value === "") {
                this.textContent = "";
                this.children = [];
            }
        },

        appendChild(element) {
            this.children.push(element);
        }
    };

    let requestedUrl;

    const context = {
        window: {
            FINALTAKE_API_BASE_URL: apiBaseUrl,
            location: {
                hostname: "127.0.0.1",
                protocol: "http:",
                search
            }
        },

        URLSearchParams,

     document: {
    getElementById: () => container,

    createElement: (tagName) => ({
        tagName,
        textContent: "",
        children: [],

        appendChild(element) {
            this.children.push(element);
        }
    })
},

        fetch: async (url) => {
            requestedUrl = url;

            // Simulate a network failure when an Error is provided.
            if (response instanceof Error) {
                throw response;
            }

            return response;
        },

        console: {
            error: () => {}
        }
    };

    runInNewContext(script, context, {
        filename: "media-details.js"
    });

    // Allow the asynchronous details request to finish.
    await new Promise((resolve) => setImmediate(resolve));

    return { container, requestedUrl };
}

test("HTTP 404 displays Media not found", async () => {
    const result = await runMediaDetails("?id=999", {
        ok: false,
        status: 404
    });

    assert.equal(
        result.requestedUrl,
        "http://127.0.0.1:5000/api/media/999"
    );

    assert.equal(
        result.container.textContent,
        "Media not found."
    );
});


test("HTTP 200 displays the correct media details", async () => {
    const result = await runMediaDetails("?id=1", {
        ok: true,
        status: 200,
        json: async () => ({
            id: "1",
            title: "The Dark Knight",
            type: "movie",
            genre: "Action",
            releaseYear: 2008
        })
    });

    // Title, image container, type, genre, year, description.
    assert.equal(result.container.children.length, 6);

    assert.deepEqual(
        result.container.children.map((element) => element.textContent),
        [
            "The Dark Knight",
            "",
            "Type: movie",
            "Genre: Action",
            "Release Year: 2008",
            "No description available."
        ]
    );
    const posterContainer = result.container.children[1];

    assert.equal(posterContainer.children.length, 1);
    assert.equal(posterContainer.children[0].tagName, "img");
    assert.equal(
        posterContainer.children[0].src,
        "../images/dark-knight.jpeg"
    );
});


test("HTTP 500 displays a generic error message", async () => {
    const result = await runMediaDetails("?id=1", {
        ok: false,
        status: 500
    });

    assert.equal(
        result.container.textContent,
        "Unable to load media details."
    );
});

test("network failure displays a generic error message", async () => {
    const result = await runMediaDetails(
        "?id=1",
        new Error("Network unavailable")
    );

    assert.equal(
        result.requestedUrl,
        "http://127.0.0.1:5000/api/media/1"
    );

    assert.equal(
        result.container.textContent,
        "Unable to load media details."
    );

    assert.equal(
        result.container.children.length,
        0
    );
});

test("media details uses configured API base URL on staging", async () => {
    const result = await runMediaDetails(
        "?id=1",
        { ok: false, status: 404 },
        "https://api.example.com"
    );

    assert.equal(
        result.requestedUrl,
        "https://api.example.com/api/media/1"
    );
});
