const { test, expect } = require("@playwright/test");

const initialMedia = {
  id: "42",
  title: "Sprint 5 Demo Movie",
  type: "movie",
  releaseYear: 2026,
  genre: "Science Fiction",
  imageUrl: null,
  description: null
};

test("manager edits prefilled media and details survive refresh", async ({ page }) => {
  let media = { ...initialMedia };
  let patchBody;
  await page.route("**/api/media/permissions", route =>
    route.fulfill({ json: { canManageMedia: true } })
  );
  await page.route("**/api/media/42", async route => {
    if (route.request().method() === "PATCH") {
      patchBody = route.request().postDataJSON();
      media = { ...media, ...patchBody };
    }
    await route.fulfill({ json: media });
  });
  await page.route("**/api/reviews**", route => route.fulfill({ json: { reviews: [] } }));

  await page.goto("http://127.0.0.1:5500/frontend/pages/media-details.html?id=42");
  await page.getByRole("link", { name: "Edit Media" }).click();
  await expect(page.locator("#media-title")).toHaveValue("Sprint 5 Demo Movie");
  await expect(page.locator("#media-type")).toHaveValue("movie");
  await expect(page.locator("#media-release-year")).toHaveValue("2026");
  await expect(page.locator("#media-genre")).toHaveValue("Science Fiction");

  await page.locator("#media-title").fill("");
  await page.getByRole("button", { name: "Save Changes" }).click();
  await expect(page.locator("#media-title-error")).toContainText("title");
  expect(patchBody).toBeUndefined();
  await page.locator("#media-title").fill(initialMedia.title);
  await page.locator("#media-release-year").fill("999");
  await page.locator("#media-image-url").fill("javascript:alert(1)");
  await page.getByRole("button", { name: "Save Changes" }).click();
  await expect(page.locator("#media-release-year-error")).toContainText("year");
  await expect(page.locator("#media-image-url-error")).toContainText("valid");
  expect(patchBody).toBeUndefined();
  await page.locator("#media-release-year").fill("2026");
  await page.locator("#media-image-url").fill("");
  await page.locator("#media-genre").fill("Adventure");
  await page.locator("#media-description").fill(
    "A sample adventure movie used to demonstrate database updates."
  );
  await page.getByRole("button", { name: "Save Changes" }).click();
  await expect(page.getByRole("status")).toContainText("Media updated successfully.");
  expect(patchBody).toEqual({
    genre: "Adventure",
    description: "A sample adventure movie used to demonstrate database updates."
  });
  await page.getByRole("link", { name: "Back to Media Details" }).click();
  await expect(page.getByText("Genre: Adventure")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Genre: Adventure")).toBeVisible();
  await expect(page.getByText(media.description)).toBeVisible();
});

test("non-manager cannot see edit link or access form", async ({ page }) => {
  await page.route("**/api/media/permissions", route =>
    route.fulfill({ json: { canManageMedia: false } })
  );
  await page.route("**/api/media/42", route => route.fulfill({ json: initialMedia }));
  await page.route("**/api/reviews**", route => route.fulfill({ json: { reviews: [] } }));
  await page.goto("http://127.0.0.1:5500/frontend/pages/media-details.html?id=42");
  await expect(page.getByRole("heading", { name: initialMedia.title })).toBeVisible();
  await expect(page.locator("#edit-media-link")).toBeHidden();
  await page.goto("http://127.0.0.1:5500/frontend/pages/edit-media.html?id=42");
  await expect(page.locator("#edit-media-notice")).toContainText("media manager");
  await expect(page.locator("#edit-media-form")).toBeHidden();
});

test("update errors remain visible without reporting success", async ({ page }) => {
  await page.route("**/api/media/permissions", route =>
    route.fulfill({ json: { canManageMedia: true } })
  );
  await page.route("**/api/media/42", route => {
    if (route.request().method() === "PATCH") {
      return route.fulfill({ status: 403, json: { error: "Permission revoked." } });
    }
    return route.fulfill({ json: initialMedia });
  });
  await page.goto("http://127.0.0.1:5500/frontend/pages/edit-media.html?id=42");
  await page.locator("#media-genre").fill("Adventure");
  await page.getByRole("button", { name: "Save Changes" }).click();
  await expect(page.locator("#edit-media-error")).toHaveText("Permission revoked.");
  await expect(page.locator("#edit-media-success")).toBeHidden();
});
