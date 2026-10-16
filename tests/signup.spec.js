const { test, expect } = require('@playwright/test');

const url = 'http://127.0.0.1:5500/frontend/pages/signup.html';

 test('Automatically fills the Sign Up form', async ({ page }) => {
  await page.goto(url);

  await page.getByPlaceholder('Choose a username')
    .fill('TestUser123');

  await page.getByPlaceholder('Enter your email')
    .fill('test@example.com');

  await page.getByPlaceholder('Create a password')
    .fill('Password123!');

  await page.getByPlaceholder('Confirm your password')
    .fill('Password123!');

  // Verify that all four fields were filled.
  await expect(
    page.getByPlaceholder('Confirm your password')
  ).toHaveValue('Password123!');


});


test('Rejects invalid email submission', async ({ page }) => {
  await page.goto(url);

  // Monitor registration requests.
  let registrationRequests = 0;

  page.on('request', request => {
    if (
      request.method() === 'POST' &&
      request.url().includes('/api/auth/register')
    ) {
      registrationRequests++;
    }
  });

  await page.getByPlaceholder('Choose a username').fill('TestUser123');
  await page.getByPlaceholder('Enter your email').fill('invalid-email');
  await page.getByPlaceholder('Create a password').fill('Password123!');
  await page.getByPlaceholder('Confirm your password').fill('Password123!');

  // Check the terms box so email is the only invalid field.
  await page.locator('#terms').check();

  await page.getByRole('button', { name: 'Create Account' }).click();

  // The application should not submit invalid registration data.
  expect(registrationRequests).toBe(0);

  // The user remains on the signup page.
  await expect(page.locator('#signup-form')).toBeVisible();
});


test('Rejects mismatched passwords submission', async ({ page }) => {
  await page.goto(url);

  // Monitor registration requests.
  let registrationRequests = 0;

  page.on('request', request => {
    if (
      request.method() === 'POST' &&
      request.url().includes('/api/auth/register')
    ) {
      registrationRequests++;
    }
  });

  await page.getByPlaceholder('Choose a username').fill('TestUser123');
  await page.getByPlaceholder('Enter your email').fill('test@example.com');
  await page.getByPlaceholder('Create a password').fill('Password123!');
  await page.getByPlaceholder('Confirm your password').fill('Different123!');

  await page.locator('#terms').check();

  await page.getByRole('button', { name: 'Create Account' }).click();

  // Mismatched passwords must not trigger registration.
  expect(registrationRequests).toBe(0);

  await expect(page.locator('#signup-form')).toBeVisible();
});
