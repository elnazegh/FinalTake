
const { test, expect } = require("@playwright/test");

const PAGE_URL =
  "http://127.0.0.1:5500/frontend/pages/review-form-demo.html?id=1";

test.beforeEach(async ({ page }) => {
  await page.goto(PAGE_URL);
});

test("Review form displays required fields", async ({ page }) => {
  await expect(page.locator("#review-form")).toBeVisible();
  await expect(page.locator("#review-rating")).toBeVisible();
  await expect(page.locator("#review-text")).toBeVisible();
  await expect(page.getByRole("button", {
    name: "Submit Review"
  })).toBeVisible();
});

test("Character counter updates while typing", async ({ page }) => {
  await page.locator("#review-text").fill("Great movie!");

  await expect(page.locator("#review-count"))
    .toHaveText("12 / 5000 characters");
});

test("Successful review submission sends correct data", async ({ page }) => {
  let submittedData = null;

  await page.route("**/api/reviews", async (route) => {
    if (route.request().method() === "POST") {
      submittedData = route.request().postDataJSON();

      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          review: {
            id: 1,
            ...submittedData
          }
        })
      });
    } else {
      await route.continue();
    }
  });

  await page.locator("#review-rating").selectOption("3.5");
  await page.locator("#review-text").fill("Great movie!");

  await page.getByRole("button", {
    name: "Submit Review"
  }).click();

  await expect(page.locator("#review-message"))
    .toHaveText("Review submitted successfully!");

  expect(submittedData).toEqual({
    media_id: "1",
    rating: 3.5,
    text: "Great movie!"
  });
});

test("Unauthenticated review submission shows login message", async ({ page }) => {
  await page.route("**/api/reviews", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({
        error: "Authentication required."
      })
    });
  });

  await page.locator("#review-rating").selectOption("4");
  await page.locator("#review-text").fill("Test review");

  await page.getByRole("button", {
    name: "Submit Review"
  }).click();

  await expect(page.locator("#review-message"))
    .toHaveText("Please log in before submitting a review.");
});

test("Backend validation error is displayed", async ({ page }) => {
  await page.route("**/api/reviews", async (route) => {
    await route.fulfill({
      status: 400,
      contentType: "application/json",
      body: JSON.stringify({
        error: "Invalid review data"
      })
    });
  });

  await page.locator("#review-rating").selectOption("2.5");
  await page.locator("#review-text").fill("Test review");

  await page.getByRole("button", {
    name: "Submit Review"
  }).click();

  await expect(page.locator("#review-message"))
    .toHaveText("Invalid review data");
});

test("Empty review cannot be submitted", async ({ page }) => {
  await page.locator("#review-rating").selectOption("3");
  await page.locator("#review-text").fill("");

  await page.getByRole("button", {
    name: "Submit Review"
  }).click();

  await expect(page.locator("#review-text"))
    .toHaveJSProperty("validity.valueMissing", true);
});
