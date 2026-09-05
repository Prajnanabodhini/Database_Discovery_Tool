(() => {
  const workspace = document.getElementById("compare-workspace");
  if (!workspace) return;
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const resultBox = document.getElementById("compare-results");
  const category = document.getElementById("compare-category");
  const search = document.getElementById("compare-search");
  const status = document.getElementById("compare-status");
  const schema = document.getElementById("compare-schema");
  const severity = document.getElementById("compare-severity");
  const database = document.getElementById("compare-database");
  const issues = document.getElementById("compare-issues");
  let comparisonId = "";
  let categoryMetadata = {};
  let currentPage = 1;

  const selectedRefs = () => ["a", "b", "c"].map(key => document.getElementById("run-" + key).value).filter(Boolean);

  function showMetadata(select) {
    const option = select.options[select.selectedIndex];
    const target = document.getElementById(select.id + "-metadata");
    target.textContent = "";
    const title = document.createElement("strong");
    title.textContent = select.value ? option.dataset.database : "No run selected";
    target.appendChild(title);
    const details = document.createElement("span");
    details.textContent = select.value
      ? [option.dataset.timestamp, option.dataset.mode, option.dataset.status, "v" + option.dataset.version,
          "SQL " + option.dataset.sqlVersion, "samples " + option.dataset.sampleRows,
          "coverage " + option.dataset.coverage, "errors " + option.dataset.errors,
          "warnings " + option.dataset.warnings, option.dataset.server].join(" · ")
      : "Select a manifested output or compatible Git export.";
    target.appendChild(details);
    if (select.value) {
      const link = document.createElement("a");
      link.href = "/run?" + new URLSearchParams({ref: select.value});
      link.textContent = "Open run metadata";
      target.appendChild(link);
    }
  }

  function refreshSourceLinks() {
    const container = document.getElementById("compare-source-links");
    container.textContent = "";
    const metadata = categoryMetadata[category.value] || {};
    const refs = selectedRefs();
    refs.forEach((ref, index) => {
      const label = ["A", "B", "C"][index];
      const runLink = document.createElement("a");
      runLink.className = "button secondary";
      runLink.href = "/run?" + new URLSearchParams({ref});
      runLink.textContent = "Run " + label + " metadata";
      container.appendChild(runLink);
      if (!metadata.availability || !metadata.availability[label] || !String(metadata.path || "").includes("/")) return;
      const separator = ref.indexOf(":");
      const root = ref.slice(0, separator);
      const relative = ref.slice(separator + 1) + "/" + metadata.path;
      const rawLink = document.createElement("a");
      rawLink.className = "button secondary";
      rawLink.href = "/raw?" + new URLSearchParams({root, path: relative});
      rawLink.textContent = "Raw source " + label;
      container.appendChild(rawLink);
    });
  }

  async function loadRows() {
    if (!comparisonId || !category.value) return;
    const query = new URLSearchParams({
      category: category.value,
      search: search.value,
      status: status.value,
      schema: schema.value,
      severity: severity.value,
      database: database.value,
      issues: issues.checked ? "true" : "false",
      page: String(currentPage),
      per_page: "100"
    });
    const response = await fetch("/api/compare/" + comparisonId + "?" + query);
    const value = await response.json();
    const body = document.getElementById("compare-rows");
    body.textContent = "";
    for (const row of value.rows || []) {
      const tr = document.createElement("tr");
      const values = [
        JSON.stringify(row.runs.A ?? null), JSON.stringify(row.runs.B ?? null), JSON.stringify(row.runs.C ?? null),
        row.intervals.A_TO_B || "", row.intervals.B_TO_C || "", row.intervals.A_TO_C || "",
        JSON.stringify(row.numeric_deltas || {})
      ];
      const identityCell = document.createElement("td");
      identityCell.appendChild(document.createTextNode(JSON.stringify(row.identity) + " "));
      const statusBadge = document.createElement("span");
      statusBadge.className = "badge " + (String(row.status).includes("CHANGED") ? "inference" : String(row.status).includes("ADDED") ? "status-completed" : String(row.status).includes("REMOVED") ? "status-failed" : "unknown");
      statusBadge.textContent = row.status;
      identityCell.appendChild(statusBadge);
      tr.appendChild(identityCell);
      for (const item of values) {
        const td = document.createElement("td");
        td.textContent = item;
        tr.appendChild(td);
      }
      const definitionCell = document.createElement("td");
      if (row.definitions) {
        const details = document.createElement("details");
        const summary = document.createElement("summary");
        summary.textContent = Object.keys(row.definition_diffs || {}).length
          ? "A/B/C definitions and interval diffs" : "A/B/C definitions";
        details.appendChild(summary);
        const grid = document.createElement("div");
        grid.className = "definition-grid";
        for (const [label, source] of Object.entries(row.definitions)) {
          const pre = document.createElement("pre");
          pre.textContent = label + "\n" + (source === null ? "NOT AVAILABLE" : source);
          grid.appendChild(pre);
        }
        details.appendChild(grid);
        for (const interval of ["A_TO_B", "B_TO_C", "A_TO_C"]) {
          if (!(row.definition_diffs || {})[interval]) continue;
          const diff = document.createElement("pre");
          diff.textContent = interval.replaceAll("_", " ") + "\n" + row.definition_diffs[interval];
          details.appendChild(diff);
        }
        definitionCell.appendChild(details);
      }
      tr.appendChild(definitionCell);
      body.appendChild(tr);
    }
    if (!(value.rows || []).length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 9;
      td.className = "empty";
      td.textContent = "No comparison rows match the current filters.";
      tr.appendChild(td);
      body.appendChild(tr);
    }
    document.getElementById("compare-range").textContent =
      "Showing " + (value.rows || []).length + " of " + value.total +
      " matching rows. Full results remain available through filters, raw sources, and explicit export.";
    const pageCount = Math.max(1, Math.ceil(value.total / value.per_page));
    document.getElementById("compare-page").textContent = "Page " + value.page + " of " + pageCount;
    document.getElementById("compare-previous").disabled = value.page <= 1;
    document.getElementById("compare-next").disabled = value.page >= pageCount;
    refreshSourceLinks();
  }

  async function run(exportFiles) {
    if (!document.getElementById("run-a").value || !document.getElementById("run-b").value) {
      document.getElementById("compare-message").textContent = "Select both Run A and Run B. Run C is optional.";
      return;
    }
    const refs = selectedRefs();
    const response = await fetch("/api/compare", {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRF-Token": token},
      body: JSON.stringify({runs: refs, export: exportFiles})
    });
    const value = await response.json();
    const message = document.getElementById("compare-message");
    if (!response.ok) {
      message.textContent = value.error || "Comparison rejected";
      return;
    }
    comparisonId = value.id;
    categoryMetadata = value.category_metadata || {};
    message.textContent = value.exports
      ? "Comparison exported: " + Object.values(value.exports).join(" · ")
      : "Comparison held in local memory; no output files created.";
    category.textContent = "";
    for (const [name, count] of Object.entries(value.categories)) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name.replaceAll("_", " ") + " (" + count + ")";
      category.appendChild(option);
    }
    document.getElementById("compare-warnings").textContent = (value.warnings || []).join(" ");
    document.getElementById("compare-semantic-note").textContent = value.semantic_note || "";
    const summary = document.getElementById("compare-summary");
    summary.textContent = "";
    for (const [key, count] of Object.entries(value.summary)) {
      const span = document.createElement("span");
      span.textContent = key + ": " + count;
      summary.appendChild(span);
    }
    database.textContent = "";
    const allDatabases = document.createElement("option");
    allDatabases.value = "";
    allDatabases.textContent = "All selected databases";
    database.appendChild(allDatabases);
    const databaseNames = [...new Set(Object.values(value.runs).map(run => run.database))];
    for (const name of databaseNames) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      database.appendChild(option);
    }
    resultBox.hidden = false;
    currentPage = 1;
    loadRows();
  }

  for (const key of ["a", "b", "c"]) {
    const select = document.getElementById("run-" + key);
    select.addEventListener("change", () => showMetadata(select));
  }
  document.getElementById("compare-now").addEventListener("click", () => run(false));
  document.getElementById("compare-export").addEventListener("click", () => run(true));
  for (const control of [category, status, severity, database, issues]) control.addEventListener("change", () => { currentPage = 1; loadRows(); });
  for (const control of [search, schema]) control.addEventListener("input", () => { currentPage = 1; loadRows(); });
  document.getElementById("compare-previous").addEventListener("click", () => { if (currentPage > 1) { currentPage -= 1; loadRows(); } });
  document.getElementById("compare-next").addEventListener("click", () => { currentPage += 1; loadRows(); });
})();
