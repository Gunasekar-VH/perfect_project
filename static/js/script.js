(() => {
  const key = "library-theme";
  const root = document.documentElement;
  const saved = localStorage.getItem(key) || "light";
  root.dataset.theme = saved;

  const applyTheme = (theme) => {
    root.dataset.theme = theme;
    localStorage.setItem(key, theme);
  };

  document.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-theme-toggle]");
    if (toggle) {
      applyTheme(root.dataset.theme === "dark" ? "light" : "dark");
    }
  });

  window.confirmDelete = () => confirm("Delete this item? This action cannot be undone.");
})();
