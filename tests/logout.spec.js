
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


test("Unauthenticated users see Login and Signup instead of Logout", async ({ page }) => {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: false })
    });
  });

  await page.goto("http://127.0.0.1:5500/frontend/index.html");

  await expect(page.locator("#logout-button")).toBeHidden();
  await expect(page.locator("#login-link")).toBeVisible();
  await expect(page.locator("#signup-link")).toBeVisible();
});

test("Authenticated users see Logout instead of Login and Signup", async ({ page }) => {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: true })
    });
  });

  await page.goto("http://127.0.0.1:5500/frontend/index.html");

  await expect(page.locator("#logout-button")).toBeVisible();
  await expect(page.locator("#login-link")).toBeHidden();
  await expect(page.locator("#signup-link")).toBeHidden();
});

test("Failed logout restores the Logout button", async ({ page }) => {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: true })
    });
  });

  await page.route("**/api/auth/logout", async (route) => {
    await route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ error: "Logout failed" })
    });
  });

  await page.goto("http://127.0.0.1:5500/frontend/index.html");

  page.on("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Unable to log out");
    await dialog.accept();
  });

  const logoutButton = page.locator("#logout-button");

  await expect(logoutButton).toBeVisible();
  await logoutButton.click();

  await expect(logoutButton).toBeEnabled();
  await expect(logoutButton).toHaveText("Log Out");
});

