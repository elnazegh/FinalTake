
const { test, expect } = require("@playwright/test");

const BASE_URL =
  "http://127.0.0.1:5500/frontend/pages/comments-demo.html";

test("Displays existing comments for a review", async ({ page }) => {
  await page.goto(`${BASE_URL}?review_id=10`);

  const comments = page.locator(".comment-card");

  await expect(comments).toHaveCount(2);
  await expect(comments.first())
    .toContainText("I agree with this review!");
  await expect(comments.nth(1))
    .toContainText("Interesting perspective.");
});

test("Allows adding a comment locally", async ({ page }) => {
  await page.goto(`${BASE_URL}?review_id=10`);

  await page.locator("#comment-text")
    .fill("This is my new comment.");

  await page.getByRole("button", {
    name: "Post Comment"
  }).click();

  await expect(page.locator(".comment-card"))
    .toHaveCount(3);

  await expect(page.locator(".comment-card").last())
    .toContainText("This is my new comment.");
});

test("Prevents empty comment submission", async ({ page }) => {
  await page.goto(`${BASE_URL}?review_id=10`);

  await page.getByRole("button", {
    name: "Post Comment"
  }).click();

  await expect(page.locator("#comment-text"))
    .toHaveJSProperty("validity.valueMissing", true);

  await expect(page.locator(".comment-card"))
    .toHaveCount(2);
});

test("Displays an empty state for another review", async ({ page }) => {
  await page.goto(`${BASE_URL}?review_id=99`);

  await expect(page.locator("#comments-message"))
    .toHaveText("No comments yet.");

  await expect(page.locator(".comment-card"))
    .toHaveCount(0);
});

test("Requires a review ID", async ({ page }) => {
  await page.goto(BASE_URL);

  await expect(page.locator("#comments-message"))
    .toHaveText("No review selected.");

  await expect(page.locator("#comment-form"))
    .toBeHidden();
});
