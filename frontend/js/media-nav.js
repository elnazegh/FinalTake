// Shows the Add Media link only to users the backend reports as media
// managers. The backend still enforces permission on every request.
document.addEventListener("DOMContentLoaded", async () => {
  const addMediaLink = document.getElementById("add-media-link");

  if (!addMediaLink) return;

  const apiBase =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
      ? `${window.location.protocol}//${window.location.hostname}:5000`
      : window.location.origin;

  try {
    const response = await fetch(`${apiBase}/api/media/permissions`, {
      credentials: "include"
    });

    if (!response.ok) return;

    const data = await response.json();
    addMediaLink.hidden = data.canManageMedia !== true;
  } catch (error) {
    console.error("Unable to check media permissions:", error);
  }
});
