
const { test, expect } = require("@playwright/test");

const PAGE_URL =
  "http://127.0.0.1:5500/frontend/pages/media-details.html?id=1";

const reviews = [
  {
    id: 101,
    user_id: 1,
    rating: 4.5,
    text: "Great movie!"
  },
  {
    id: 102,
    user_id: 2,
    rating: 3,
    text: "Good movie."
  }
];

test.beforeEach(async ({ page }) => {
  await page.route("**/api/reviews?media_id=1", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ reviews })
    });
  });
});

test("Review owner sees Edit and Delete buttons", async ({ page }) => {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user_id: 1
      })
    });
  });

  await page.goto(PAGE_URL);

  const cards = page.locator(".review-card");

  await expect(cards).toHaveCount(2);
  await expect(cards.nth(0).getByRole("button", { name: "Edit" }))
    .toBeVisible();
  await expect(cards.nth(0).getByRole("button", { name: "Delete" }))
    .toBeVisible();

  await expect(cards.nth(1).getByRole("button", { name: "Edit" }))
    .toHaveCount(0);
  await expect(cards.nth(1).getByRole("button", { name: "Delete" }))
    .toHaveCount(0);
});

test("Unauthenticated users cannot see Edit or Delete", async ({ page }) => {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: false })
    });
  });

  await page.goto(PAGE_URL);

  await expect(page.locator(".review-card")).toHaveCount(2);
  await expect(page.getByRole("button", { name: "Edit" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Delete" })).toHaveCount(0);
});

test("Review owner can submit an edit request", async ({ page }) => {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user_id: 1
      })
    });
  });

  let editRequestReceived = false;

  await page.route("**/api/reviews/101", async (route) => {
    if (route.request().method() === "PATCH") {
      const body = route.request().postDataJSON();

      expect(body.text).toBe("Updated movie review");

      editRequestReceived = true;

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Review updated"
        })
      });
    } else {
      await route.continue();
    }
  });

  await page.goto(PAGE_URL);

  page.once("dialog", async (dialog) => {
    expect(dialog.type()).toBe("prompt");
    await dialog.accept("Updated movie review");
  });

  await page.locator(".review-card").first()
    .getByRole("button", { name: "Edit" })
    .click();

  await expect.poll(() => editRequestReceived).toBe(true);
});

test("Review owner can submit a delete request", async ({ page }) => {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user_id: 1
      })
    });
  });

  let deleteRequestReceived = false;

  await page.route("**/api/reviews/101", async (route) => {
    if (route.request().method() === "DELETE") {
      deleteRequestReceived = true;

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Review deleted"
        })
      });
    } else {
      await route.continue();
    }
  });

  await page.goto(PAGE_URL);

  page.once("dialog", async (dialog) => {
    expect(dialog.type()).toBe("confirm");
    await dialog.accept();
  });

  await page.locator(".review-card").first()
    .getByRole("button", { name: "Delete" })
    .click();

  await expect.poll(() => deleteRequestReceived).toBe(true);
});

test("HTTP 403 prevents unauthorized review editing", async ({ page }) => {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user_id: 1
      })
    });
  });

  let patchAttempts = 0;

  await page.route("**/api/reviews/101", async (route) => {
    if (route.request().method() === "PATCH") {
      patchAttempts++;

      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ error: "Forbidden" })
      });
    } else {
      await route.continue();
    }
  });

  await page.goto(PAGE_URL);

  const messages = [];

  page.on("dialog", async (dialog) => {
    if (dialog.type() === "prompt") {
      await dialog.accept("Unauthorized change");
    } else {
      messages.push(dialog.message());
      await dialog.accept();
    }
  });

  await page.locator(".review-card").first()
    .getByRole("button", { name: "Edit" })
    .click();

  await expect.poll(() => patchAttempts).toBe(1);

  await expect.poll(() =>
    messages.some((message) =>
      message.includes("not authorized")
    )
  ).toBe(true);

  await expect(page.locator(".review-card").first())
    .toContainText("Great movie!");
});

test("HTTP 403 prevents unauthorized review deletion", async ({ page }) => {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user_id: 1
      })
    });
  });

  let deleteAttempts = 0;

  await page.route("**/api/reviews/101", async (route) => {
    if (route.request().method() === "DELETE") {
      deleteAttempts++;

      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ error: "Forbidden" })
      });
    } else {
      await route.continue();
    }
  });

  await page.goto(PAGE_URL);

  const messages = [];

  page.on("dialog", async (dialog) => {
    if (dialog.type() === "confirm") {
      await dialog.accept();
    } else {
      messages.push(dialog.message());
      await dialog.accept();
    }
  });

  await page.locator(".review-card").first()
    .getByRole("button", { name: "Delete" })
    .click();

  await expect.poll(() => deleteAttempts).toBe(1);

  await expect.poll(() =>
    messages.some((message) =>
      message.includes("not authorized")
    )
  ).toBe(true);

  await expect(page.locator(".review-card").first())
    .toContainText("Great movie!");
});


test("Canceling review deletion sends no DELETE request", async ({ page }) => {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user_id: 1
      })
    });
  });

  let deleteAttempts = 0;

  await page.route("**/api/reviews/101", async (route) => {
    if (route.request().method() === "DELETE") {
      deleteAttempts++;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: "{}"
    });
  });

  await page.goto(PAGE_URL);

  page.once("dialog", async (dialog) => {
    expect(dialog.type()).toBe("confirm");
    await dialog.dismiss();
  });

  await page.locator(".review-card").first()
    .getByRole("button", { name: "Delete" })
    .click();

  await expect(page.locator(".review-card").first())
    .toContainText("Great movie!");

  expect(deleteAttempts).toBe(0);
});
