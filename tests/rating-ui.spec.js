
const { test, expect } = require("@playwright/test");

const PAGE_URL =
  "http://127.0.0.1:5500/frontend/pages/rating-demo.html";

test.beforeEach(async ({ page }) => {
  await page.goto(PAGE_URL);
});

test("Displays five stars and ten rating choices", async ({ page }) => {
  await expect(page.locator(".rating-star")).toHaveCount(5);
  await expect(page.locator(".rating-half")).toHaveCount(10);

  await expect(page.locator(".rating-value"))
    .toHaveText("No rating selected");
});

test("Selects a half-star rating of 0.5", async ({ page }) => {
  await page.getByRole("button", {
    name: "0.5 out of 5 stars"
  }).click();

  await expect(page.locator(".rating-value"))
    .toHaveText("Selected rating: 0.5 / 5");

  await expect(page.locator(".rating-star").first()
    .locator(".star-fill"))
    .toHaveCSS("width", "22px");
});

test("Selects a rating of 3.5 stars", async ({ page }) => {
  await page.getByRole("button", {
    name: "3.5 out of 5 stars"
  }).click();

  await expect(page.locator(".rating-value"))
    .toHaveText("Selected rating: 3.5 / 5");

  await expect(page.getByRole("button", {
    name: "3.5 out of 5 stars"
  })).toHaveAttribute("aria-pressed", "true");
});


test("Selects the maximum rating of 5 stars", async ({ page }) => {
  await page.getByRole("button", {
    name: "5 out of 5 stars",
    exact: true
  }).click();

  await expect(page.locator(".rating-value"))
    .toHaveText("Selected rating: 5.0 / 5");

  await expect(page.locator(".rating-star").last()
    .locator(".star-fill"))
    .toHaveCSS("width", "44px");
});


test("Supports keyboard rating selection", async ({ page }) => {
  const ratingButton = page.getByRole("button", {
    name: "2.5 out of 5 stars"
  });

  await ratingButton.focus();
  await page.keyboard.press("Enter");

  await expect(page.locator(".rating-value"))
    .toHaveText("Selected rating: 2.5 / 5");
});

test("Updates the rating when another value is selected", async ({ page }) => {
  await page.getByRole("button", {
    name: "1 out of 5 stars",
    exact: true
  }).click();

  await page.getByRole("button", {
    name: "4.5 out of 5 stars"
  }).click();

  await expect(page.locator(".rating-value"))
    .toHaveText("Selected rating: 4.5 / 5");
});
