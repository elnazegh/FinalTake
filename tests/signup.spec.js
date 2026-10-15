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

test('Rejects invalid email', async ({ page }) => {
  await page.goto(url);

  await page.getByPlaceholder('Choose a username').fill('TestUser123');
  await page.getByPlaceholder('Enter your email').fill('invalid-email');
  await page.getByPlaceholder('Create a password').fill('Password123!');
  await page.getByPlaceholder('Confirm your password').fill('Password123!');

  const email = page.getByPlaceholder('Enter your email');

  // Check the browser's email validation.
  const isValid = await email.evaluate(input => input.checkValidity());

  expect(isValid).toBe(false);
});

test('Detects mismatched passwords', async ({ page }) => {
  await page.goto(url);

  await page.getByPlaceholder('Choose a username').fill('TestUser123');
  await page.getByPlaceholder('Enter your email').fill('test@example.com');
  await page.getByPlaceholder('Create a password').fill('Password123!');
  await page.getByPlaceholder('Confirm your password').fill('Different123!');

  const password = await page.getByPlaceholder('Create a password').inputValue();
  const confirmPassword = await page.getByPlaceholder('Confirm your password').inputValue();

  expect(password).not.toBe(confirmPassword);
});
