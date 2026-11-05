
document.addEventListener("DOMContentLoaded", () => {
  const spoilerToggle = document.getElementById("spoiler-toggle");
  const spoilerContent = document.getElementById("spoiler-content");
  const spoilerPlaceholder = document.getElementById("spoiler-placeholder");

  if (!spoilerToggle || !spoilerContent || !spoilerPlaceholder) {
    return;
  }

  function setSpoilerVisibility(isRevealed) {
    spoilerContent.hidden = !isRevealed;
    spoilerPlaceholder.hidden = isRevealed;

    spoilerToggle.textContent = isRevealed
      ? "Hide Spoiler"
      : "Show Spoiler";

    spoilerToggle.setAttribute(
      "aria-expanded",
      String(isRevealed)
    );
  }

  // Hide spoiler content when the page first loads.
  setSpoilerVisibility(false);

  spoilerToggle.addEventListener("click", () => {
    const isCurrentlyRevealed =
      spoilerToggle.getAttribute("aria-expanded") === "true";

    setSpoilerVisibility(!isCurrentlyRevealed);
  });
});
