const form = document.querySelector("#profile-form");
const statusBox = document.querySelector("#status");
const submitButton = document.querySelector("#submit-button");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusBox.textContent = "";
  statusBox.className = "";
  submitButton.disabled = true;
  submitButton.innerHTML = "Finding your matches…";

  const fd = new FormData(form);
  const payload = Object.fromEntries(fd.entries());
  payload.skills = (payload.skills || "").split(",").map(s => s.trim()).filter(Boolean);

  try {
    const response = await fetch("/api/recommend", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not generate recommendations.");

    renderRecommendations(data.recommendations);
    document.querySelector("#result-summary").textContent =
      `Hi ${data.student.name} — these roles are ranked for your ${data.student.branch} profile. Matching method: ${data.matching_method}.`;
    document.querySelector("#results-count").textContent =
      `${data.recommendations.length} opportunities`;
    document.querySelector("#results-section").hidden = false;
    statusBox.className = "success";
    statusBox.textContent = "Profile saved. Your recommendations are ready.";
    document.querySelector("#results-section").scrollIntoView({behavior: "smooth", block: "start"});
  } catch (error) {
    statusBox.textContent = error.message + " Check that the Flask server is running.";
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = 'Find my matches <span>→</span>';
  }
});

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[ch]));
}

function renderRecommendations(items) {
  const root = document.querySelector("#recommendations");
  root.innerHTML = items.map(item => {
    const matched = item.matched_skills.length
      ? item.matched_skills.map(s => `<span class="skill">${escapeHtml(s)}</span>`).join("")
      : '<span class="pill">No exact skill overlap yet</span>';
    const missing = item.missing_skills.length
      ? item.missing_skills.map(s => `<span class="skill missing">${escapeHtml(s)}</span>`).join("")
      : '<span class="skill">All listed skills matched</span>';
    const safeUrl = /^https?:\/\//i.test(item.apply_url) ? item.apply_url : "#";
    return `
      <article class="internship-card">
        <div class="card-top">
          <div><div class="company">${escapeHtml(item.company)}</div><h3>${escapeHtml(item.title)}</h3></div>
          <div class="score">${item.match_score}%<small>MATCH</small></div>
        </div>
        <p class="description">${escapeHtml(item.description)}</p>
        <div class="meta">
          <span class="pill">⌖ ${escapeHtml(item.location)}</span>
          <span class="pill">${escapeHtml(item.work_mode)}</span>
          <span class="pill">${escapeHtml(item.duration)}</span>
        </div>
        <div class="skills-title">Skills you match</div><div class="skill-list">${matched}</div>
        <div class="skills-title">Skills to develop</div><div class="skill-list">${missing}</div>
        <div class="card-bottom"><span class="stipend">${escapeHtml(item.stipend)}</span>
          <a class="apply-link" href="${safeUrl}" target="_blank" rel="noopener noreferrer">Explore opportunity ↗</a>
        </div>
      </article>`;
  }).join("");
}
