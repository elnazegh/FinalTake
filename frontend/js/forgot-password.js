
const API_BASE_URL =
    window.FINALTAKE_API_BASE_URL ||
    (
        ["localhost", "127.0.0.1"].includes(window.location.hostname)
            ? `${window.location.protocol}//${window.location.hostname}:5000`
            : window.location.origin
    );

const forgotPasswordForm = document.getElementById("forgot-password-form");
const message = document.getElementById("forgot-password-message");

forgotPasswordForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    // Get the email entered by the user
    const email = document.getElementById("email").value.trim();
    const submitButton = forgotPasswordForm.querySelector('button[type="submit"]');

    // Prevent multiple requests
    submitButton.disabled = true;
    submitButton.textContent = "Sending...";
    message.textContent = "";

    try {
        // Send the email to the Flask backend
        const response = await fetch(
            `${API_BASE_URL}/api/auth/forgot-password`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email })
            }
        );

        const result = await response.json();

        if (response.ok) {
            message.textContent = result.message;
            forgotPasswordForm.reset();
        } else {
            message.textContent = result.error || "Unable to send reset link.";
        }

    } catch (error) {
        message.textContent = "Unable to connect to the server.";

    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Send Reset Link";
    }
});
