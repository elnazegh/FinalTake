console.log("signup.js loaded");

const signupForm = document.getElementById("signup-form");

if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        
        console.log("Signup form submitted");

        const username = document.getElementById("username").value.trim();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword =
            document.getElementById("confirm-password").value;

        if (password !== confirmPassword) {
            alert("Passwords do not match.");
            return;
        }

        try {
            const response = await fetch(
                "http://127.0.0.1:5000/api/auth/register",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        username: username,
                        email: email,
                        password: password
                    })
                }
            );

            const data = await response.json();

            if (response.ok) {
                alert(data.message || "Account created successfully.");
                signupForm.reset();
            } else {
                alert(data.error || "Registration failed.");
            }

        } catch (error) {
            console.error("Registration request failed:", error);
            alert("Unable to connect to the server.");
        }
    });
}