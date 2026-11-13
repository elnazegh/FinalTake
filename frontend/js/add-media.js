const ADD_MEDIA_API_BASE =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? `${window.location.protocol}//${window.location.hostname}:5000`
    : window.location.origin;

const MAX_TITLE_LENGTH = 255;
const MAX_GENRE_LENGTH = 100;
const MAX_IMAGE_URL_LENGTH = 500;
const MAX_DESCRIPTION_LENGTH = 5000;
const MIN_RELEASE_YEAR = 1000;
const MAX_RELEASE_YEAR = new Date().getFullYear() + 10;

const addMediaForm = document.getElementById("add-media-form");
const addMediaIntro = document.getElementById("add-media-intro");
const addMediaNotice = document.getElementById("add-media-notice");
const addMediaError = document.getElementById("add-media-error");
const addMediaSubmit = document.getElementById("add-media-submit");
const addMediaSuccess = document.getElementById("add-media-success");
const createdMediaId = document.getElementById("created-media-id");
const createdMediaTitle = document.getElementById("created-media-title");
const addAnotherButton = document.getElementById("add-another-media");

const titleInput = document.getElementById("media-title");
const typeSelect = document.getElementById("media-type");
const yearInput = document.getElementById("media-release-year");
const genreInput = document.getElementById("media-genre");
const imageUrlInput = document.getElementById("media-image-url");
const descriptionInput = document.getElementById("media-description");

const fieldInputs = {
  title: titleInput,
  type: typeSelect,
  releaseYear: yearInput,
  genre: genreInput,
  imageUrl: imageUrlInput,
  description: descriptionInput
};

const fieldErrorIds = {
  title: "media-title-error",
  type: "media-type-error",
  releaseYear: "media-release-year-error",
  genre: "media-genre-error",
  imageUrl: "media-image-url-error",
  description: "media-description-error"
};

function showFieldError(field, message) {
  document.getElementById(fieldErrorIds[field]).textContent = message;
  fieldInputs[field].setAttribute("aria-invalid", "true");
}

function clearErrors() {
  Object.keys(fieldInputs).forEach((field) => {
    document.getElementById(fieldErrorIds[field]).textContent = "";
    fieldInputs[field].removeAttribute("aria-invalid");
  });

  addMediaError.hidden = true;
  addMediaError.textContent = "";
}

function showFormError(message) {
  addMediaError.textContent = message;
  addMediaError.hidden = false;
}

function isHttpUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch (error) {
    return false;
  }
}

// Returns the request body, or null after displaying validation errors.
function validateForm() {
  clearErrors();

  const title = titleInput.value.trim();
  const type = typeSelect.value;
  const yearText = yearInput.value.trim();
  const genre = genreInput.value.trim();
  const imageUrl = imageUrlInput.value.trim();
  const description = descriptionInput.value.trim();
  let releaseYear = null;
  let valid = true;

  if (!title) {
    showFieldError("title", "Title is required.");
    valid = false;
  } else if (title.length > MAX_TITLE_LENGTH) {
    showFieldError(
      "title",
      `Title cannot exceed ${MAX_TITLE_LENGTH} characters.`
    );
    valid = false;
  }

  if (!type) {
    showFieldError("type", "Select a media type.");
    valid = false;
  }

  if (yearText) {
    releaseYear = Number(yearText);

    if (
      !Number.isInteger(releaseYear) ||
      releaseYear < MIN_RELEASE_YEAR ||
      releaseYear > MAX_RELEASE_YEAR
    ) {
      showFieldError(
        "releaseYear",
        `Enter a year between ${MIN_RELEASE_YEAR} and ${MAX_RELEASE_YEAR}.`
      );
      valid = false;
    }
  }

  if (genre.length > MAX_GENRE_LENGTH) {
    showFieldError(
      "genre",
      `Genre cannot exceed ${MAX_GENRE_LENGTH} characters.`
    );
    valid = false;
  }

  if (imageUrl) {
    if (imageUrl.length > MAX_IMAGE_URL_LENGTH) {
      showFieldError(
        "imageUrl",
        `Image URL cannot exceed ${MAX_IMAGE_URL_LENGTH} characters.`
      );
      valid = false;
    } else if (!isHttpUrl(imageUrl)) {
      showFieldError("imageUrl", "Enter a valid http or https URL.");
      valid = false;
    }
  }

  if (description.length > MAX_DESCRIPTION_LENGTH) {
    showFieldError(
      "description",
      `Description cannot exceed ${MAX_DESCRIPTION_LENGTH} characters.`
    );
    valid = false;
  }

  if (!valid) {
    const firstInvalid = addMediaForm.querySelector("[aria-invalid]");
    if (firstInvalid) firstInvalid.focus();
    return null;
  }

  return {
    title,
    type,
    releaseYear,
    genre: genre || null,
    imageUrl: imageUrl || null,
    description: description || null
  };
}

function showNotice(message) {
  addMediaForm.hidden = true;
  addMediaNotice.textContent = message;
  addMediaNotice.hidden = false;
}

// The backend enforces permissions. This only decides what to display.
async function checkMediaPermission() {
  try {
    const response = await fetch(
      `${ADD_MEDIA_API_BASE}/api/media/permissions`,
      { credentials: "include" }
    );

    if (!response.ok) {
      throw new Error(`Permission check failed (${response.status})`);
    }

    const data = await response.json();

    if (data.canManageMedia === true) {
      addMediaForm.hidden = false;
      return;
    }

    showNotice(
      "You need to log in with a media manager account to add media."
    );
  } catch (error) {
    console.error("Unable to check media permissions:", error);
    showNotice("Unable to verify your permissions. Please try again later.");
  }
}

addMediaForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const body = validateForm();

  if (!body) return;

  addMediaSubmit.disabled = true;
  addMediaSubmit.textContent = "Adding...";

  try {
    const response = await fetch(`${ADD_MEDIA_API_BASE}/api/media`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      showFormError(data.error || "Unable to add media. Please try again.");
      return;
    }

    createdMediaId.textContent = data.id;
    createdMediaTitle.textContent = data.media.title;
    addMediaForm.hidden = true;
    addMediaIntro.hidden = true;
    addMediaSuccess.hidden = false;
    addAnotherButton.focus();
  } catch (error) {
    console.error("Add media request failed:", error);
    showFormError("Unable to reach the server. Please try again.");
  } finally {
    addMediaSubmit.disabled = false;
    addMediaSubmit.textContent = "Add Media";
  }
});

addAnotherButton.addEventListener("click", () => {
  addMediaForm.reset();
  clearErrors();
  addMediaSuccess.hidden = true;
  addMediaIntro.hidden = false;
  addMediaForm.hidden = false;
  titleInput.focus();
});

checkMediaPermission();
