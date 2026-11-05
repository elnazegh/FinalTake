
function createRatingSelector(container, onChange = () => {}) {
  if (!container) {
    throw new Error("Rating container is required.");
  }

  let selectedRating = 0;

  const wrapper = document.createElement("div");
  wrapper.className = "rating-selector";

  const stars = document.createElement("div");
  stars.className = "rating-stars";
  stars.setAttribute("role", "group");
  stars.setAttribute("aria-label", "Select a rating from 0.5 to 5 stars");

  const output = document.createElement("p");
  output.className = "rating-value";
  output.setAttribute("aria-live", "polite");
  output.textContent = "No rating selected";

  function updateRating(value) {
    selectedRating = value;

    output.textContent =
      `Selected rating: ${value.toFixed(1)} / 5`;

    stars.querySelectorAll(".rating-star").forEach((star) => {
      const starNumber = Number(star.dataset.star);
      const fill = star.querySelector(".star-fill");

      const percentage = Math.max(
        0,
        Math.min(100, (value - (starNumber - 1)) * 100)
      );

      fill.style.width = `${percentage}%`;
    });

    stars.querySelectorAll(".rating-half").forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        String(Number(button.dataset.rating) === value)
      );
    });

    onChange(value);
  }

  for (let starNumber = 1; starNumber <= 5; starNumber++) {
    const star = document.createElement("div");
    star.className = "rating-star";
    star.dataset.star = String(starNumber);

    const background = document.createElement("span");
    background.className = "star-background";
    background.textContent = "★";
    background.setAttribute("aria-hidden", "true");

    const fill = document.createElement("span");
    fill.className = "star-fill";
    fill.textContent = "★";
    fill.setAttribute("aria-hidden", "true");

    for (const value of [starNumber - 0.5, starNumber]) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "rating-half";
      button.dataset.rating = String(value);
      button.setAttribute("aria-label", `${value} out of 5 stars`);
      button.setAttribute("aria-pressed", "false");

      button.addEventListener("click", () => {
        updateRating(value);
      });

      star.appendChild(button);
    }

    star.prepend(background, fill);
    stars.appendChild(star);
  }

  wrapper.append(stars, output);
  container.replaceChildren(wrapper);

  return {
    getValue: () => selectedRating
  };
}
