const EDIT_API_BASE =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? `${window.location.protocol}//${window.location.hostname}:5000`
    : window.location.origin;
const editMediaId = new URLSearchParams(window.location.search).get("id");
const editForm = document.getElementById("edit-media-form");
const editNotice = document.getElementById("edit-media-notice");
const editError = document.getElementById("edit-media-error");
const editSuccess = document.getElementById("edit-media-success");
const editSubmit = document.getElementById("edit-media-submit");
const editFields = {
  title: document.getElementById("media-title"),
  type: document.getElementById("media-type"),
  releaseYear: document.getElementById("media-release-year"),
  genre: document.getElementById("media-genre"),
  imageUrl: document.getElementById("media-image-url"),
  description: document.getElementById("media-description")
};
const editErrorIds = {
  title: "media-title-error",
  type: "media-type-error",
  releaseYear: "media-release-year-error",
  genre: "media-genre-error",
  imageUrl: "media-image-url-error",
  description: "media-description-error"
};
let originalMedia;

function showEditNotice(message) {
  editForm.hidden = true;
  editNotice.textContent = message;
  editNotice.hidden = false;
}

function setFieldError(field, message) {
  document.getElementById(editErrorIds[field]).textContent = message;
  editFields[field].setAttribute("aria-invalid", "true");
}

function validateEditForm() {
  for (const field of Object.keys(editFields)) {
    document.getElementById(editErrorIds[field]).textContent = "";
    editFields[field].removeAttribute("aria-invalid");
  }
  editError.hidden = true;
  editSuccess.hidden = true;
  const title = editFields.title.value.trim();
  const type = editFields.type.value;
  const yearText = editFields.releaseYear.value.trim();
  const genre = editFields.genre.value.trim();
  const imageUrl = editFields.imageUrl.value.trim();
  const description = editFields.description.value.trim();
  const maxYear = new Date().getFullYear() + 10;
  let valid = true;

  if (!title || title.length > 255) {
    setFieldError("title", "Enter a title of at most 255 characters.");
    valid = false;
  }
  if (!["movie", "tv", "book", "game"].includes(type)) {
    setFieldError("type", "Select a media type.");
    valid = false;
  }
  const releaseYear = yearText ? Number(yearText) : null;
  if (yearText && (!Number.isInteger(releaseYear) ||
      releaseYear < 1000 || releaseYear > maxYear)) {
    setFieldError("releaseYear", `Enter a year between 1000 and ${maxYear}.`);
    valid = false;
  }
  if (genre.length > 100) {
    setFieldError("genre", "Genre cannot exceed 100 characters.");
    valid = false;
  }
  if (imageUrl) {
    let validUrl = false;
    try {
      const url = new URL(imageUrl);
      validUrl = url.protocol === "http:" || url.protocol === "https:";
    } catch (error) {
      validUrl = false;
    }
    if (imageUrl.length > 500 || !validUrl) {
      setFieldError("imageUrl", "Enter a valid http or https URL of at most 500 characters.");
      valid = false;
    }
  }
  if (description.length > 5000) {
    setFieldError("description", "Description cannot exceed 5000 characters.");
    valid = false;
  }
  if (!valid) {
    const firstInvalid = editForm.querySelector("[aria-invalid]");
    if (firstInvalid) firstInvalid.focus();
    return null;
  }
  return {
    title, type, releaseYear, genre: genre || null,
    imageUrl: imageUrl || null, description: description || null
  };
}

async function loadEditForm() {
  if (!editMediaId) {
    showEditNotice("Media not found.");
    return;
  }
  const encodedId = encodeURIComponent(editMediaId);
  document.getElementById("back-to-media").href = `media-details.html?id=${encodedId}`;
  try {
    const permissionResponse = await fetch(`${EDIT_API_BASE}/api/media/permissions`, {
      credentials: "include"
    });
    if (!permissionResponse.ok) throw new Error("Permission check failed");
    const permission = await permissionResponse.json();
    if (permission.canManageMedia !== true) {
      showEditNotice("You need to log in with a media manager account to edit media.");
      return;
    }
    const response = await fetch(`${EDIT_API_BASE}/api/media/${encodedId}`);
    if (response.status === 404) {
      showEditNotice("Media not found.");
      return;
    }
    if (!response.ok) throw new Error("Media request failed");
    originalMedia = await response.json();
    for (const field of Object.keys(editFields)) {
      editFields[field].value = originalMedia[field] ?? "";
    }
    editForm.hidden = false;
  } catch (error) {
    console.error("Unable to load edit form:", error);
    showEditNotice("Unable to load media or verify your permissions. Please try again later.");
  }
}

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = validateEditForm();
  if (!values) return;
  const changes = Object.fromEntries(
    Object.entries(values).filter(([field, value]) => value !== originalMedia[field])
  );
  if (Object.keys(changes).length === 0) {
    editSuccess.textContent = "No changes to save.";
    editSuccess.hidden = false;
    return;
  }
  editSubmit.disabled = true;
  editSubmit.textContent = "Saving...";
  try {
    const response = await fetch(
      `${EDIT_API_BASE}/api/media/${encodeURIComponent(editMediaId)}`,
      {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(changes)
      }
    );
    const data = await response.json();
    if (!response.ok) {
      editError.textContent = data.error || "Unable to update media. Please try again.";
      editError.hidden = false;
      return;
    }
    originalMedia = data;
    editSuccess.textContent = "Media updated successfully.";
    editSuccess.hidden = false;
  } catch (error) {
    console.error("Media update request failed:", error);
    editError.textContent = "Unable to update media. Please try again.";
    editError.hidden = false;
  } finally {
    editSubmit.disabled = false;
    editSubmit.textContent = "Save Changes";
  }
});

loadEditForm();
