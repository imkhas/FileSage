"use strict";

const PANELS = ["organize", "smart", "watch", "search"];
let lastSeq = 0;
let api = null;

const $ = (id) => document.getElementById(id);

function setStatus(text) {
  $("status-bar").textContent = text;
}

function log(panel, text, cls) {
  const el = document.createElement("div");
  el.className = "line" + (cls ? " " + cls : "");
  el.textContent = text;
  const logEl = $("log-" + panel);
  logEl.appendChild(el);
  logEl.scrollTop = logEl.scrollHeight;
}

function setBusy(panel, busy) {
  const spinner = $(panel + "-spinner");
  if (spinner) spinner.hidden = !busy;
  document
    .querySelectorAll('#panel-' + panel + " .btn")
    .forEach((b) => (b.disabled = busy));
}

async function runAction(panel, fn, doneText) {
  setBusy(panel, true);
  try {
    const result = await fn();
    if (doneText) setStatus(doneText);
    return result;
  } catch (err) {
    log(panel, "Error: " + (err && err.message ? err.message : err));
    setStatus("Action failed.");
    return null;
  } finally {
    setBusy(panel, false);
  }
}

// ---------------- Navigation ----------------

function switchPanel(name) {
  document.querySelectorAll(".nav-item").forEach((b) => {
    b.classList.toggle("active", b.dataset.panel === name);
  });
  document.querySelectorAll(".panel").forEach((p) => {
    p.classList.toggle("active", p.id === "panel-" + name);
  });
}

// ---------------- Live log polling ----------------

async function pollLogs() {
  try {
    const res = await api.get_logs(lastSeq);
    if (!res || !res.entries || res.entries.length === 0) return;
    for (const entry of res.entries) {
      lastSeq = entry[0];
      log(entry[1], entry[2], entry[3] || "");
    }
  } catch (e) {
    // bridge or page not ready
  }
}

// ---------------- Folder bar ----------------

async function pickFolder() {
  try {
    const path = await api.pick_folder();
    if (path) $("folder-path").value = path;
  } catch (err) {
    log("organize", "Folder picker failed: " + (err.message || err));
  }
}

// ---------------- Handlers ----------------

function folderPath() {
  return $("folder-path").value.trim();
}

function init() {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => switchPanel(btn.dataset.panel));
  });

  $("browse-btn").addEventListener("click", pickFolder);

  $("menu-toggle").addEventListener("click", () => {
    document.getElementById("app").classList.toggle("sidebar-hidden");
  });

  $("org-preview").addEventListener("click", () =>
    runAction("organize", () => api.organize(folderPath(), true, $("org-recursive").checked), "Organize preview finished.")
  );

  $("org-apply").addEventListener("click", () =>
    runAction("organize", () => api.organize(folderPath(), false, $("org-recursive").checked), "Organize finished.")
  );

  $("org-undo").addEventListener("click", () =>
    runAction("organize", () => api.undo(folderPath()), "Undo finished.")
  );

  $("smart-analyze").addEventListener("click", () =>
    runAction("smart", () => api.analyze(folderPath(), $("smart-recursive").checked), "Analysis finished.")
  );

  $("smart-apply").addEventListener("click", () =>
    runAction(
      "smart",
      () =>
        api.apply_smart(
          folderPath(),
          $("smart-moves").checked,
          $("smart-renames").checked,
          $("smart-dups").checked
        ),
      "Smart apply finished."
    )
  );

  $("watch-toggle").addEventListener("change", async () => {
    const on = $("watch-toggle").checked;
    const path = folderPath();
    if (on && !path) {
      log("watch", "Enter a folder path first.");
      $("watch-toggle").checked = false;
      return;
    }
    const msg = await runAction("watch", () => api.set_watching(path, on));
    if (msg && on === false) $("watch-toggle").checked = false;
  });

  async function doSearch() {
    const query = $("search-query").value.trim();
    if (!query) {
      log("search", "Type a search query first.");
      return;
    }
    await runAction(
      "search",
      () => api.search(query, parseInt($("search-limit").value, 10) || 10)
    );
  }

  $("search-btn").addEventListener("click", doSearch);
  $("search-query").addEventListener("keydown", (e) => {
    if (e.key === "Enter") doSearch();
  });

  $("index-btn").addEventListener("click", () =>
    runAction(
      "search",
      () => api.index_folder($("index-folder").value.trim() || folderPath()),
      "Indexing finished."
    )
  );

  $("build-vectors-btn").addEventListener("click", () =>
    runAction("search", () => api.build_vectors(), "Vector build finished.")
  );

  $("status-btn").addEventListener("click", () =>
    runAction("search", () => api.index_status())
  );

  setStatus("Ready.");
  setInterval(pollLogs, 400);
  pollLogs();
}

if (window.pywebview && window.pywebview.api) {
  api = window.pywebview.api;
  init();
} else {
  window.addEventListener("pywebviewready", () => {
    api = window.pywebview.api;
    init();
  });
}
