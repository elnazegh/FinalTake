const API_BASE_URL = "http://127.0.0.1:5000/api/auth";

document.addEventListener("DOMContentLoaded", () => {
  const signupForm = document.getElementById("signup-form");
  const loginForm = document.getElementById("login-form");

  // Sign Up API
  if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const usernameElement = document.getElementById("username");
      const emailElement = document.getElementById("email");
      const passwordElement = document.getElementById("password");
      const confirmPasswordElement =
        document.getElementById("confirm-password");
      const termsElement = document.getElementById("terms");

      // Do not send API request if validation fails
      if (
        !usernameElement.value.trim() ||
        !emailElement.value.trim() ||
        !emailElement.checkValidity() ||
        passwordElement.value.length < 8 ||
        passwordElement.value !== confirmPasswordElement.value ||
        !termsElement.checked
      ) {
        return;
      }

      const username = usernameElement.value.trim();
      const email = emailElement.value.trim();
      const password = passwordElement.value;

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
          alert(data.error || "Registration failed.");
          return;
        }

        alert(data.message || "Account created successfully!");
      } catch (error) {
        console.error("Registration error:", error);
        alert("Unable to connect to the server.");
      }
    });
  }

  // Login API
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const emailElement = document.getElementById("email");
      const passwordElement = document.getElementById("password");

      // Do not send API request if validation fails
      if (
        !emailElement.value.trim() ||
        !emailElement.checkValidity() ||
        !passwordElement.value.trim()
      ) {
        return;
      }

      const email = emailElement.value.trim();
      const password = passwordElement.value;

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
        alert("Unable to connect to the server.");
      }
    });
  }
});