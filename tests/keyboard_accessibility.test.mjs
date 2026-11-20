import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(
    new URL("../frontend/index.html", import.meta.url),
    "utf8"
);

const css = readFileSync(
    new URL("../frontend/css/style.css", import.meta.url),
    "utf8"
);

test("search controls have associated accessible labels", () => {
    const controls = [
        "media-search",
        "genre-filter",
        "media-type-filter",
        "sort-filter"
    ];

    for (const id of controls) {
        assert.match(
            html,
            new RegExp(`<label\\s+for="${id}"`),
            `Missing accessible label for ${id}`
        );

        assert.match(
            html,
            new RegExp(`<(?:input|select)\\b[^>]*\\bid="${id}"`),
            `Missing search control ${id}`
        );
    }
});

test("keyboard focus styling includes interactive controls", () => {
    const focusRule = css.match(
        /([^{}]+)\{\s*outline:\s*3px solid #38bdf8;/
    );

    assert.ok(focusRule, "Missing visible focus outline");

    const selectors = focusRule[1];

    for (const selector of [
        "a:focus-visible",
        "button:focus-visible",
        "input:focus-visible",
        "select:focus-visible"
    ]) {
        assert.ok(
            selectors.includes(selector),
            `Missing focus style for ${selector}`
        );
    }
});
