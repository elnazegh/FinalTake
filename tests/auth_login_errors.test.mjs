
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const script = readFileSync(
    new URL("../frontend/js/auth-api.js", import.meta.url),
    "utf8"
);

// Execute the actual frontend login code with simulated API responses.
async function simulateLogin(fetchImplementation) {
    const alerts = [];
    let onPageReady;
    let onSubmit;

    const button = {
        textContent: "Login",
        disabled: false
    };

    const loginForm = {
        querySelector: () => button,
        addEventListener: (event, callback) => {
            if (event === "submit") {
                onSubmit = callback;
            }
        }
    };

    const elements = {
        "signup-form": null,
        "login-form": loginForm,
        "email": {
            value: "test678@example.com",
            checkValidity: () => true
        },
        "password": {
            value: "TestPassword123"
        }
    };

    const context = {
        document: {
            addEventListener: (event, callback) => {
                if (event === "DOMContentLoaded") {
                    onPageReady = callback;
                }
            },
            getElementById: (id) => elements[id] ?? null
        },
        fetch: fetchImplementation,
        alert: (message) => alerts.push(message),
        console: {
            error: () => {}
        }
    };

    runInNewContext(script, context, {
        filename: "auth-api.js"
    });

    assert.equal(typeof onPageReady, "function");
    onPageReady();

    assert.equal(typeof onSubmit, "function");

    let defaultPrevented = false;

    await onSubmit({
        preventDefault: () => {
            defaultPrevented = true;
        }
    });

    return { alerts, button, defaultPrevented };
}

 test("HTTP 503 displays authentication service error", async () => {
    let request;

    const result = await simulateLogin(async (url, options) => {
        request = {
            url,
            method: options.method,
            body: JSON.parse(options.body)
        };

        return {
            ok: false,
            status: 503,
            json: async () => ({
                error: "Authentication service unavailable"
            })
        };
    });

    assert.equal(
        request.url,
        "http://127.0.0.1:5000/api/auth/login"
    );

    assert.equal(request.method, "POST");
    assert.equal(request.body.email, "test678@example.com");

    assert.deepEqual(result.alerts, [
        "Authentication service unavailable"
    ]);

    assert.equal(result.button.disabled, false);
    assert.equal(result.button.textContent, "Login");
    assert.equal(result.defaultPrevented, true);
});

test("HTTP 401 displays invalid credentials error", async () => {
    let request;

    const result = await simulateLogin(async (url, options) => {
        request = {
            url,
            method: options.method,
            body: JSON.parse(options.body)
        };

        return {
            ok: false,
            status: 401,
            json: async () => ({
                error: "Invalid credentials"
            })
        };
    });

    assert.equal(
        request.url,
        "http://127.0.0.1:5000/api/auth/login"
    );

    assert.equal(request.method, "POST");
    assert.equal(request.body.email, "test678@example.com");
    assert.equal(request.body.password, "TestPassword123");

    assert.deepEqual(result.alerts, [
        "Invalid credentials"
    ]);

    assert.equal(result.button.disabled, false);
    assert.equal(result.button.textContent, "Login");
    assert.equal(result.defaultPrevented, true);
});

test("Network failure displays an error and restores Login button", async () => {
    const result = await simulateLogin(async () => {
        throw new Error("Network connection failed");
    });

    assert.deepEqual(result.alerts, [
        "Unable to connect to the server. Please try again."
    ]);

    assert.equal(result.button.disabled, false);
    assert.equal(result.button.textContent, "Login");
    assert.equal(result.defaultPrevented, true);
});
