
const REVIEWS_API_BASE =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? `${window.location.protocol}//${window.location.hostname}:5000`
    : window.location.origin;

const reviewsList = document.getElementById("reviews-list");
const reviewsMessage = document.getElementById("reviews-message");

async function getCurrentUserId() {
  try {
    const response = await fetch(
      `${REVIEWS_API_BASE}/api/auth/session`,
      { credentials: "include" }
    );

    if (!response.ok) {
      return null;
    }

    const data = await response.json();

    return data.authenticated === true
      ? data.user_id
      : null;
  } catch (error) {
    console.error("Unable to check user session:", error);
    return null;
  }
}

async function editReview(review) {
  const newText = window.prompt(
    "Edit your review:",
    review.text
  );

  if (newText === null) return;

  const trimmedText = newText.trim();

  if (!trimmedText) {
    alert("Review cannot be empty.");
    return;
  }

  if (trimmedText.length > 5000) {
    alert("Review cannot exceed 5000 characters.");
    return;
  }

  try {
    const response = await fetch(
      `${REVIEWS_API_BASE}/api/reviews/${encodeURIComponent(review.id)}`,
      {
        method: "PATCH",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: trimmedText })
      }
    );

    if (response.status === 401 || response.status === 403) {
      alert("You are not authorized to edit this review.");
      await loadReviews();
      return;
    }

    if (!response.ok) {
      throw new Error("Review update failed");
    }

    await loadReviews();
  } catch (error) {
    console.error("Unable to edit review:", error);
    alert("Unable to update review. Please try again.");
  }
}


async function deleteReview(review) {
  const confirmed = window.confirm(
    "Are you sure you want to delete this review?"
  );

  if (!confirmed) return;

  try {
    const response = await fetch(
      `${REVIEWS_API_BASE}/api/reviews/${encodeURIComponent(review.id)}`,
      {
        method: "DELETE",
        credentials: "include"
      }
    );

    if (response.status === 401 || response.status === 403) {
      alert("You are not authorized to delete this review.");
      await loadReviews();
      return;
    }

    if (!response.ok) {
      throw new Error("Review deletion failed");
    }

    await loadReviews();
  } catch (error) {
    console.error("Unable to delete review:", error);
    alert("Unable to delete review. Please try again.");
  }
}



async function loadReviews() {
  const mediaId = new URLSearchParams(
    window.location.search
  ).get("id");

  if (!mediaId) {
    reviewsMessage.textContent = "No media selected.";
    return;
  }

  try {
    const response = await fetch(
      `${REVIEWS_API_BASE}/api/reviews?media_id=${encodeURIComponent(mediaId)}`,
      { credentials: "include" }
    );

    if (!response.ok) {
      throw new Error("Unable to retrieve reviews");
    }

    const data = await response.json();
    const reviews = data.reviews || [];
    const currentUserId = await getCurrentUserId();

    reviewsList.replaceChildren();

    if (reviews.length === 0) {
      reviewsMessage.textContent = "No reviews yet.";
      return;
    }

    reviewsMessage.textContent = "";

    reviews.forEach((review) => {
      const card = document.createElement("article");
      card.className = "review-card";

      const rating = document.createElement("p");
      rating.textContent = `Rating: ${review.rating}/5`;

      const text = document.createElement("p");
      text.textContent = review.text;

     
card.append(rating, text);

if (
  currentUserId !== null &&
  String(currentUserId) === String(review.user_id)
) {
  const actions = document.createElement("div");
  actions.className = "review-actions";

  const editButton = document.createElement("button");
  editButton.type = "button";
  editButton.textContent = "Edit";

  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.textContent = "Delete";

  editButton.addEventListener("click", () => {
  editReview(review);
});

deleteButton.addEventListener("click", () => {
  deleteReview(review);
});

  actions.append(editButton, deleteButton);
  card.appendChild(actions);
}

reviewsList.appendChild(card);

    });
  } catch (error) {
    reviewsMessage.textContent =
      "Unable to load reviews. Please try again.";
    console.error("Review loading failed:", error);
  }
}

loadReviews();
