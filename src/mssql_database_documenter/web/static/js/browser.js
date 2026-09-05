(() => {
  document.querySelectorAll(".file-list a").forEach(link =>
    link.addEventListener("keydown", event => {
      if (event.key === "Enter") link.click();
    })
  );

  const copy = document.getElementById("copy-raw");
  if (!copy) return;
  copy.addEventListener("click", async () => {
    const status = document.getElementById("copy-status");
    try {
      const response = await fetch(copy.dataset.rawUrl);
      if (!response.ok) throw new Error("Raw source request failed");
      const source = await response.text();
      await navigator.clipboard.writeText(source);
      status.textContent = "Full canonical SQL source copied.";
    } catch (error) {
      status.textContent = "Copy was unavailable. Use Open raw or Download to access the full source.";
    }
  });
})();
