(() => {
  const controls = document.getElementById("execution-controls");
  if (!controls) return;
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const status = document.getElementById("job-status");
  const log = document.getElementById("job-log");
  const warning = document.getElementById("job-warning");
  const cancel = document.getElementById("cancel-job");
  const exportButton = document.getElementById("create-git-export");
  const exportSelect = document.getElementById("git-run-select");
  const exportMessage = document.getElementById("git-export-message");
  const finalStatuses = ["COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED", "CANCELLED"];
  let timer;

  const set = (id, value, fallback = "—") => {
    document.getElementById(id).textContent = value || fallback;
  };

  function present(job) {
    status.dataset.active = job.id || "";
    status.querySelector("strong").textContent = job.status || "IDLE";
    status.querySelector("span").textContent = job.current_stage || "No discovery job is active.";
    status.querySelector("i").style.width = (job.progress || 0) + "%";
    set("job-id", job.id);
    set("job-database", job.database);
    set("job-mode", job.mode);
    set("job-started", job.started_utc);
    set("job-finished", job.finished_utc);
    set("job-elapsed", String(job.elapsed_seconds || 0) + "s", "0s");
    warning.textContent = job.error || (job.warnings || []).join(" · ") || "No warnings or errors reported.";
    log.textContent = (job.logs || ["Waiting for a predefined action…"]).join("\n");
  }

  async function poll() {
    try {
      const response = await fetch("/api/jobs/current");
      const job = await response.json();
      present(job);
      if (job.id && !finalStatuses.includes(job.status)) timer = setTimeout(poll, 1000);
    } catch (error) {
      log.textContent = "Local status request failed.";
    }
  }

  async function start(action, confirmHeavy) {
    if (confirmHeavy && !confirm("Full read-only profiling can consume database resources even though it cannot modify data. Continue?")) return;
    const database = document.getElementById("database-select").value;
    const response = await fetch("/api/jobs/" + encodeURIComponent(action), {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRF-Token": token},
      body: JSON.stringify({database})
    });
    const value = await response.json();
    if (!response.ok) {
      log.textContent = value.error || "Action rejected";
      return;
    }
    present(value);
    poll();
  }

  controls.querySelectorAll("[data-action]").forEach(button =>
    button.addEventListener("click", () => start(button.dataset.action, button.dataset.confirm === "true"))
  );
  cancel.addEventListener("click", async () => {
    await fetch("/api/jobs/cancel", {method: "POST", headers: {"X-CSRF-Token": token}});
    poll();
  });
  if (exportButton) {
    exportButton.addEventListener("click", async () => {
      if (!exportSelect.value) {
        exportMessage.textContent = "Select an output run first.";
        return;
      }
      const response = await fetch("/api/git-export", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRF-Token": token},
        body: JSON.stringify({run_ref: exportSelect.value})
      });
      const value = await response.json();
      exportMessage.textContent = response.ok
        ? "Git export queued as controlled job " + value.id + "."
        : value.error || "Git export rejected.";
      if (response.ok) {
        present(value);
        poll();
      }
    });
  }
  status.querySelector("i").style.width = (status.dataset.progress || 0) + "%";
  poll();
})();
