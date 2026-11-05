
const REVIEW_API_BASE =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? `${window.location.protocol}//${window.location.hostname}:5000`
    : window.location.origin;

const reviewForm = document.getElementById("review-form");
const reviewRating = document.getElementById("review-rating");
const reviewText = document.getElementById("review-text");
const reviewCount = document.getElementById("review-count");
const reviewMessage = document.getElementById("review-message");

const MAX_REVIEW_LENGTH = 5000;

reviewText.addEventListener("input", () => {
  reviewCount.textContent =
    `${reviewText.value.length} / ${MAX_REVIEW_LENGTH} characters`;
});

reviewForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const mediaId = new URLSearchParams(
    window.location.search
  ).get("id");

  const rating = Number(reviewRating.value);
  const text = reviewText.value.trim();

  reviewMessage.textContent = "";

  if (!mediaId) {
    reviewMessage.textContent = "No media selected.";
    return;
  }

  if (
    !reviewRating.value ||
    !Number.isFinite(rating) ||
    rating < 0.5 ||
    rating > 5 ||
    !Number.isInteger(rating * 2)
  ) {
    reviewMessage.textContent =
      "Select a rating from 0.5 to 5 stars.";
    return;
  }

  if (!text) {
    reviewMessage.textContent =
      "Review cannot be empty.";
    return;
  }

  if (text.length > MAX_REVIEW_LENGTH) {
    reviewMessage.textContent =
      "Review cannot exceed 5000 characters.";
    return;
  }

  const submitButton = reviewForm.querySelector(
    'button[type="submit"]'
  );

  submitButton.disabled = true;
  reviewMessage.textContent = "Submitting review...";

  try {
    const response = await fetch(
      `${REVIEW_API_BASE}/api/reviews`,
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          media_id: mediaId,
          rating,
          text
        })
      }
    );

    if (response.status === 401) {
      reviewMessage.textContent =
        "Please log in before submitting a review.";
      return;
    }

    const data = await response.json();

    if (!response.ok) {
      reviewMessage.textContent =
        data.error || "Unable to submit review.";
      return;
    }

    reviewMessage.textContent =
      "Review submitted successfully!";

    reviewForm.reset();
    reviewCount.textContent =
      `0 / ${MAX_REVIEW_LENGTH} characters`;

  } catch (error) {
    console.error("Review submission failed:", error);

    reviewMessage.textContent =
      "Unable to connect to the server. Please try again.";
  } finally {
    submitButton.disabled = false;
  }
});
