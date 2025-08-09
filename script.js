// Tabs
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    // Remove active class from all tabs and tab-panels
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    
    // Add active class to the clicked tab and corresponding tab panel
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

// Form submit
const form = document.getElementById("reportForm");
const result = document.getElementById("result");

if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    result.textContent = "Sending…";
    result.className = "result";

    try {
      const data = new FormData(form); // handles files too
      const res = await fetch("/api/report", { method: "POST", body: data });
      const json = await res.json();

      if (!json.ok) {
        result.textContent = json.message || "There was a problem submitting your report.";
        result.className = "result error";
        return;
      }

      result.textContent = json.message || "Report received. Thank you!";
      result.className = "result success";
      form.reset();
    } catch (err) {
      result.textContent = "Network error. Please try again.";
      result.className = "result error";
    }
  });
}
