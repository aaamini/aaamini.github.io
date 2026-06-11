document.addEventListener("click", (ev) => {
  const btn = ev.target.closest("[data-toggle]");
  if (!btn) return;
  const el = document.getElementById(btn.dataset.toggle);
  if (el) el.hidden = !el.hidden;
});
