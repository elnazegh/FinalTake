
const { test, expect } = require("@playwright/test");

test("Logout button appears and redirects after successful logout", async ({ page }) => {
  // Simulate an authenticated user.
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: true })
    });
  });

  // Simulate successful logout.
  await page.route("**/api/auth/logout", async (route) => {
    expect(route.request().method()).toBe("POST");

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ message: "Logout successful" })
    });
  });

 await page.goto("http://127.0.0.1:5500/frontend/index.html");

  const logoutButton = page.getByRole("button", {
    name: "Log Out"
  });

  await expect(logoutButton).toBeVisible();

  await logoutButton.click();

  await expect(page).toHaveURL(/\/pages\/login\.html$/);
});
