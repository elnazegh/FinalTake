document.addEventListener("DOMContentLoaded", () => {
  const signupForm = document.getElementById("signup-form");

  if (signupForm) {
    signupForm.addEventListener("submit", (event) => {
      event.preventDefault();

      const email = document.getElementById("email");
      const password = document.getElementById("password");
      const confirmPassword = document.getElementById("confirm-password");
      const terms = document.getElementById("terms");

      if (!email.value.trim()) {
        alert("Please enter your email.");
        email.focus();
        return;
      }

      if (!email.checkValidity()) {
        alert("Please enter a valid email address.");
        email.focus();
        return;
      }

      if (password.value.length < 8) {
        alert("Password must be at least 8 characters.");
        password.focus();
        return;
      }

      if (password.value !== confirmPassword.value) {
        alert("Passwords do not match.");
        confirmPassword.focus();
        return;
      }

      if (!terms.checked) {
        alert("Please agree to the Terms and Privacy Policy.");
        terms.focus();
        return;
      }

      alert("Sign Up form is valid.");
    });
  }

  const loginForm = document.getElementById("login-form");

  if (loginForm) {
    loginForm.addEventListener("submit", (event) => {
      event.preventDefault();

      const email = document.getElementById("email");
      const password = document.getElementById("password");

      if (!email.value.trim()) {
        alert("Please enter your email.");
        email.focus();
        return;
      }

      if (!email.checkValidity()) {
        alert("Please enter a valid email address.");
        email.focus();
        return;
      }

      if (!password.value.trim()) {
        alert("Please enter your password.");
        password.focus();
        return;
      }

      alert("Login form is valid.");
    });
  }
});