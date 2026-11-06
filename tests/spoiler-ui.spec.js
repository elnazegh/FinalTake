
const { test, expect } = require("@playwright/test");

const BASE_URL =
  "http://127.0.0.1:5500/frontend/pages/spoiler-demo.html";

test("Spoiler content is hidden by default", async ({ page }) => {
  await page.goto(BASE_URL);

  await expect(page.locator("#spoiler-content"))
    .toBeHidden();

  await expect(page.locator("#spoiler-placeholder"))
    .toBeVisible();

  await expect(page.locator("#spoiler-toggle"))
    .toHaveAttribute("aria-expanded", "false");
});

test("Show Spoiler reveals hidden content", async ({ page }) => {
  await page.goto(BASE_URL);

  await page.getByRole("button", {
    name: "Show Spoiler"
  }).click();

  await expect(page.locator("#spoiler-content"))
    .toBeVisible();

  await expect(page.locator("#spoiler-placeholder"))
    .toBeHidden();

  await expect(page.locator("#spoiler-toggle"))
    .toHaveAttribute("aria-expanded", "true");
});

test("Hide Spoiler conceals content again", async ({ page }) => {
  await page.goto(BASE_URL);

  await page.getByRole("button", {
    name: "Show Spoiler"
  }).click();

  await page.getByRole("button", {
    name: "Hide Spoiler"
  }).click();

  await expect(page.locator("#spoiler-content"))
    .toBeHidden();

  await expect(page.locator("#spoiler-toggle"))
    .toHaveAttribute("aria-expanded", "false");
});

test("Spoiler toggle supports keyboard interaction", async ({ page }) => {
  await page.goto(BASE_URL);

  await page.locator("#spoiler-toggle").focus();
  await page.keyboard.press("Enter");

  await expect(page.locator("#spoiler-content"))
    .toBeVisible();

  await page.keyboard.press("Space");

  await expect(page.locator("#spoiler-content"))
    .toBeHidden();
});

test("Spoiler content remains hidden after page reload", async ({ page }) => {
  await page.goto(BASE_URL);

  await page.getByRole("button", {
    name: "Show Spoiler"
  }).click();

  await expect(page.locator("#spoiler-content"))
    .toBeVisible();

  await page.reload();

  await expect(page.locator("#spoiler-content"))
    .toBeHidden();
});
