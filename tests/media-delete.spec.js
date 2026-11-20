const { test, expect } = require("@playwright/test");

const media = {
  id: "42", title: "Sprint 5 Demo Movie", type: "movie",
  releaseYear: 2026, genre: "Adventure"
};
const detailsUrl = "http://127.0.0.1:5500/frontend/pages/media-details.html?id=42";

async function setup(page, canManageMedia, deleteResponse = 200) {
  let deleted = false;
  let requests = 0;
  let releaseDelete;
  const pending = new Promise(resolve => { releaseDelete = resolve; });
  await page.route("**/api/media/permissions", route =>
    route.fulfill({ json: { canManageMedia } })
  );
  await page.route("**/api/media/42", async route => {
    if (route.request().method() === "DELETE") {
      requests++;
      await pending;
      if (deleteResponse === 200) deleted = true;
      return route.fulfill({ status: deleteResponse, json: { message: "done" } });
    }
    return deleted
      ? route.fulfill({ status: 404, json: { error: "Not found" } })
      : route.fulfill({ json: media });
  });
  await page.route("**/api/reviews**", route => route.fulfill({ json: { reviews: [] } }));
  await page.route("**/api/search**", route =>
    route.fulfill({ json: { results: deleted ? [] : [media] } })
  );
  return { releaseDelete, getRequests: () => requests };
}

test("manager can cancel then confirm deletion and find no result after refresh", async ({ page }) => {
  const state = await setup(page, true);
  await page.goto(detailsUrl);
  const button = page.getByRole("button", { name: "Delete Media" });
  await expect(button).toBeVisible();
  page.once("dialog", async dialog => {
    expect(dialog.message()).toContain(media.title);
    await dialog.dismiss();
  });
  await button.click();
  expect(state.getRequests()).toBe(0);
  await expect(page.getByRole("heading", { name: media.title })).toBeVisible();
  page.once("dialog", dialog => dialog.accept());
  await button.click();
  await expect(button).toBeDisabled();
  expect(state.getRequests()).toBe(1);
  state.releaseDelete();
  await expect(page.locator("#delete-media-message")).toContainText("deleted successfully");
  await expect(button).toBeHidden();
  await page.reload();
  await expect(page.locator("#media-details")).toHaveText("Media not found.");
  await page.getByRole("link", { name: "Back to Search" }).click();
  await page.locator("#media-search").fill(media.title);
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.locator("#search-results-grid")).not.toContainText(media.title);
});

test("non-manager cannot see Delete Media", async ({ page }) => {
  await setup(page, false);
  await page.goto(detailsUrl);
  await expect(page.getByRole("heading", { name: media.title })).toBeVisible();
  await expect(page.locator("#delete-media-button")).toBeHidden();
});

for (const [status, message] of [
  [403, "not authorized"],
  [404, "not found or already deleted"],
  [500, "Unable to delete media"],
  [202, "Unable to delete media"]
]) {
  test(`delete failure ${status} does not report success`, async ({ page }) => {
    const state = await setup(page, true, status);
    state.releaseDelete();
    await page.goto(detailsUrl);
    page.once("dialog", dialog => dialog.accept());
    await page.getByRole("button", { name: "Delete Media" }).click();
    await expect(page.locator("#delete-media-message")).toContainText(message);
    await expect(page.locator("#delete-media-button")).toBeEnabled();
    await expect(page.getByRole("heading", { name: media.title })).toBeVisible();
  });
}
