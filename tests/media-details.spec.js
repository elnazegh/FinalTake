
const { test, expect } = require("@playwright/test");

test("Displays media description and image from API", async ({ page }) => {
  // Mock the media details API response.
  await page.route("**/api/media/1", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "1",
        title: "The Dark Knight",
        type: "movie",
        genre: "Action",
        releaseYear: 2008,
        description: "A superhero film set in Gotham City.",
        imageUrl: "/frontend/images/test-poster.png"
      })
    });
  });

  // Provide a valid test image without adding image files.
  await page.route("**/frontend/images/test-poster.png", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "image/svg+xml",
      body: `<svg xmlns="http://www.w3.org/2000/svg"
                  width="200" height="300">
               <rect width="200" height="300" fill="#24334a"/>
             </svg>`
    });
  });

  await page.goto(
    "http://127.0.0.1:5500/frontend/pages/media-details.html?id=1"
  );

  await expect(
    page.getByRole("heading", { name: "The Dark Knight" })
  ).toBeVisible();

  await expect(
    page.getByText("A superhero film set in Gotham City.")
  ).toBeVisible();

  await expect(
    page.getByText("Genre: Action")
  ).toBeVisible();

  const image = page.locator(".media-details-image");

  await expect(image).toBeVisible();

  // Verify that the image actually loaded.
  await expect.poll(async () =>
    image.evaluate((img) => img.complete && img.naturalWidth > 0)
  ).toBe(true);
});
