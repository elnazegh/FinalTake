const API_BASE_URL = "http://127.0.0.1:5000/api/auth";

document.addEventListener("DOMContentLoaded", () => {
  const signupForm = document.getElementById("signup-form");
  const loginForm = document.getElementById("login-form");

  // Sign Up API
  if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const username = document.getElementById("username").value.trim();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;
      const submitButton = signupForm.querySelector('button[type="submit"]');

      const originalText = submitButton.textContent;
      submitButton.disabled = true;
      submitButton.textContent = "Creating Account...";

      try {
        const response = await fetch(`${API_BASE_URL}/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            username,
            email,
            password
          })
        });

        const data = await response.json();

        if (!response.ok) {
          alert(data.error || data.message || "Registration failed.");
          return;
        }

        alert(data.message || "Account created successfully!");
      } catch (error) {
        console.error("Registration error:", error);
        alert("Unable to connect to the server. Please try again.");
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = originalText;
      }
    });
  }

  // Login API
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;
      const submitButton = loginForm.querySelector('button[type="submit"]');

      const originalText = submitButton.textContent;
      submitButton.disabled = true;
      submitButton.textContent = "Logging In...";

      try {
        const response = await fetch(`${API_BASE_URL}/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            email,
            password
          })
        });

        const data = await response.json();

        if (!response.ok) {
          alert(data.error || data.message || "Login failed.");
          return;
        }

        alert(data.message || "Login successful!");
      } catch (error) {
        console.error("Login error:", error);
        alert("Unable to connect to the server. Please try again.");
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = originalText;
      }
    });
  }
});