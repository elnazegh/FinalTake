
const AUTH_API_URL = "http://127.0.0.1:5000/api/auth";

document.addEventListener("DOMContentLoaded", async () => {
  const logoutButton = document.getElementById("logout-button");
  const loginLink = document.getElementById("login-link");
  const signupLink = document.getElementById("signup-link");

  if (!logoutButton) return;

  function updateNavigation(isAuthenticated) {
    logoutButton.hidden = !isAuthenticated;
    if (loginLink) loginLink.hidden = isAuthenticated;
    if (signupLink) signupLink.hidden = isAuthenticated;
  }

  // Hide logout until the backend confirms a session.
logoutButton.hidden = true;
if (loginLink) loginLink.hidden = true;
if (signupLink) signupLink.hidden = true;

  try {
    const response = await fetch(`${AUTH_API_URL}/session`, {
      method: "GET",
      credentials: "include"
    });

    if (response.ok) {
  const data = await response.json();
  updateNavigation(data.authenticated === true);
} else {
  updateNavigation(false);
}
  } catch (error) {
    console.error("Unable to check login session:", error);
    updateNavigation(false);
  }

  logoutButton.addEventListener("click", async () => {
    logoutButton.disabled = true;
    logoutButton.textContent = "Logging Out...";

    try {
      const response = await fetch(`${AUTH_API_URL}/logout`, {
        method: "POST",
        credentials: "include"
      });

      if (!response.ok) {
        throw new Error("Logout request failed");
      }

      // Redirect only after successful logout.
      window.location.href = "pages/login.html";
    } catch (error) {
      console.error("Logout error:", error);
      alert("Unable to log out. Please try again.");
      logoutButton.disabled = false;
      logoutButton.textContent = "Log Out";
    }
  });
});
