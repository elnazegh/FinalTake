
const resetForm = document.getElementById("reset-password-form");
const resetMessage = document.getElementById("reset-password-message");
const resetButton = resetForm.querySelector('button[type="submit"]');

// Read the reset token from the email link
const params = new URLSearchParams(window.location.search);
const resetToken = params.get("token");

// Remove the token from the visible URL after reading it
if (resetToken) {
    window.history.replaceState(
        null,
        "",
        window.location.pathname
    );
}

if (!resetToken) {
    resetMessage.textContent =
        "Invalid or missing reset link. Please request a new one.";
    resetButton.disabled = true;
}

resetForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const password = document.getElementById("password").value;
    const confirmPassword =
        document.getElementById("confirm-password").value;

    // Check that both passwords match
    if (password !== confirmPassword) {
        resetMessage.textContent = "Passwords do not match.";
        return;
    }

    // Check minimum password length
    if (password.length < 8) {
        resetMessage.textContent =
            "Password must be at least 8 characters.";
        return;
    }

    if (!resetToken) {
        resetMessage.textContent =
            "Invalid or missing reset link.";
        return;
    }

    resetButton.disabled = true;
    resetButton.textContent = "Resetting...";
    resetMessage.textContent = "";

    try {
        const response = await fetch(
            "http://127.0.0.1:5000/api/auth/reset-password",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    token: resetToken,
                    password: password
                })
            }
        );

        const result = await response.json();

        if (response.ok) {
            resetMessage.textContent =
                "Password reset successful! You can now log in.";

            resetForm.reset();
            resetButton.textContent = "Password Updated";
        } else {
            resetMessage.textContent =
                result.error || "Password reset failed.";

            resetButton.disabled = false;
            resetButton.textContent = "Reset Password";
        }

    } catch (error) {
        resetMessage.textContent =
            "Unable to connect to the server.";

        resetButton.disabled = false;
        resetButton.textContent = "Reset Password";
    }
});
