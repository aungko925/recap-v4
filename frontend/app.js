const API_BASE_URL = window.RECAP_API_URL || "http://localhost:8000";

const form = document.querySelector("#recap-form");
const videoInput = document.querySelector("#video-file");
const fileName = document.querySelector("#file-name");
const message = document.querySelector("#form-message");
const submitButton = form.querySelector("button[type='submit']");
const resultPanel = document.querySelector("#result-panel");

videoInput.addEventListener("change", () => {
  fileName.textContent = videoInput.files[0]?.name || "Choose a video to upload";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "Inspecting your video...";
  message.dataset.state = "loading";
  submitButton.disabled = true;
  resultPanel.hidden = true;

  try {
    const response = await fetch(`${API_BASE_URL}/api/recap`, {
      method: "POST",
      body: new FormData(form),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "The video could not be prepared.");
    }

    document.querySelector("#result-title").textContent = data.title;
    const details = document.querySelector("#result-details");
    details.replaceChildren();
    addDetail(details, "Duration", formatDuration(data.video.duration_seconds));
    addDetail(details, "Resolution", `${data.video.width} × ${data.video.height}`);
    addDetail(details, "Audio track", data.video.has_audio ? "Present" : "Not detected");
    addDetail(details, "Language", data.language === "my" ? "Burmese" : "English");
    document.querySelector("#result-note").textContent = data.message;
    resultPanel.hidden = false;
    message.textContent = "Your recap request is ready.";
    message.dataset.state = "success";
  } catch (error) {
    message.textContent = error instanceof TypeError
      ? "Could not reach the API. Start the backend and try again."
      : error.message;
    message.dataset.state = "error";
  } finally {
    submitButton.disabled = false;
  }
});

function addDetail(list, label, value) {
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = label;
  description.textContent = value;
  list.append(term, description);
}

function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round(seconds % 60);
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}
