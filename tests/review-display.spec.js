
const { test, expect } = require("@playwright/test");

const BASE_URL =
  "http://127.0.0.1:5500/frontend/pages/media-details.html";

test("Displays review ratings and text", async ({ page }) => {
  await page.route("**/api/reviews?media_id=1", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        reviews: [
          {
            id: 101,
            user_id: 1,
            rating: 4.5,
            text: "Excellent movie!"
          },
          {
            id: 102,
            user_id: 2,
            rating: 3,
            text: "Good movie."
          }
        ]
      })
    });
  });

  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: false })
    });
  });

  await page.goto(`${BASE_URL}?id=1`);

  const cards = page.locator(".review-card");

  await expect(cards).toHaveCount(2);
  await expect(cards.nth(0)).toContainText("Rating: 4.5/5");
  await expect(cards.nth(0)).toContainText("Excellent movie!");
  await expect(cards.nth(1)).toContainText("Rating: 3/5");
  await expect(cards.nth(1)).toContainText("Good movie.");
});

test("Requests reviews for the selected media ID", async ({ page }) => {
  let requestedMediaId = null;

  await page.route("**/api/reviews?media_id=42", async (route) => {
    requestedMediaId = new URL(route.request().url())
      .searchParams.get("media_id");

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ reviews: [] })
    });
  });

  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: false })
    });
  });

  await page.goto(`${BASE_URL}?id=42`);

  await expect.poll(() => requestedMediaId).toBe("42");
  await expect(page.locator("#reviews-message"))
    .toHaveText("No reviews yet.");
});

test("Displays a message when no reviews exist", async ({ page }) => {
  await page.route("**/api/reviews?media_id=1", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ reviews: [] })
    });
  });

  await page.goto(`${BASE_URL}?id=1`);

  await expect(page.locator("#reviews-message"))
    .toHaveText("No reviews yet.");

  await expect(page.locator(".review-card")).toHaveCount(0);
});

test("Displays an error when review loading fails", async ({ page }) => {
  await page.route("**/api/reviews?media_id=1", async (route) => {
    await route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ error: "Server error" })
    });
  });

  await page.goto(`${BASE_URL}?id=1`);

  await expect(page.locator("#reviews-message"))
    .toHaveText("Unable to load reviews. Please try again.");
});
