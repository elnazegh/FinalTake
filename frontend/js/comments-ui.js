
function createCommentsInterface() {
  const commentsList = document.getElementById("comments-list");
  const commentsMessage = document.getElementById("comments-message");
  const commentForm = document.getElementById("comment-form");
  const commentText = document.getElementById("comment-text");

  const reviewId = new URLSearchParams(
    window.location.search
  ).get("review_id");

  // Temporary demo data only.
  // Replace with backend API data after integration.
  const demoComments = [
    {
      id: 1,
      review_id: "10",
      username: "MovieFan",
      text: "I agree with this review!"
    },
    {
      id: 2,
      review_id: "10",
      username: "BookLover",
      text: "Interesting perspective."
    }
  ];

  const comments = [];

  function renderComments() {
    commentsList.replaceChildren();

    if (comments.length === 0) {
      commentsMessage.textContent = "No comments yet.";
      return;
    }

    commentsMessage.textContent = "";

    comments.forEach((comment) => {
      const card = document.createElement("article");
      card.className = "comment-card";

      const author = document.createElement("strong");
      author.textContent = comment.username;

      const text = document.createElement("p");
      text.textContent = comment.text;

      card.append(author, text);
      commentsList.appendChild(card);
    });
  }

  if (!reviewId) {
    commentsMessage.textContent = "No review selected.";
    commentForm.hidden = true;
    return;
  }

  comments.push(
    ...demoComments.filter(
      (comment) => comment.review_id === reviewId
    )
  );

  renderComments();

  commentForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const text = commentText.value.trim();

    if (!text) {
      commentsMessage.textContent =
        "Comment cannot be empty.";
      return;
    }

    comments.push({
      id: Date.now(),
      review_id: reviewId,
      username: "Demo User",
      text
    });

    commentForm.reset();
    renderComments();
  });
}

document.addEventListener(
  "DOMContentLoaded",
  createCommentsInterface
);
