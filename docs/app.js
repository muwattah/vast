const API = localStorage.getItem("vast_api") || "http://127.0.0.1:8000/api";

const fmtEuro = (v) => {
  if (v == null || isNaN(v)) return "–";
  return "€" + Math.round(v).toLocaleString("nl-BE");
};

async function fetchJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    const page = btn.dataset.page;
    document.getElementById("page-" + page)?.classList.add("active");
    if (page === "dashboard") loadDashboard();
    if (page === "properties") loadProperties();
    if (page === "deals") loadDeals();
    if (page === "sources") loadSources();
    if (page === "map") loadMap();
  });
});

async function loadDashboard() {
  const el = document.getElementById("dash-stats");
  const dealsEl = document.getElementById("dash-deals");
  try {
    const stats = await fetchJSON(API + "/data-mode/stats").catch(() => null);
    const health = await fetchJSON(API.replace(/\/api$/, "") + "/health").catch(() => null);
    if (!health) {
      el.innerHTML = "<p class='muted'>API niet bereikbaar. Start: <code>python -m uvicorn backend.main:app --port 8000</code></p>";
      return;
    }
    el.innerHTML = `
      <div class="stat"><div class="num">${stats?.real_listings ?? "–"}</div><div class="lbl">Real listings</div></div>
      <div class="stat"><div class="num">${stats?.demo_listings ?? "–"}</div><div class="lbl">DEMO</div></div>
      <div class="stat"><div class="num">${stats?.total ?? "–"}</div><div class="lbl">Totaal</div></div>`;
    const props = await fetchJSON(API + "/properties?exclude_demo=true&limit=12");
    const list = props.items || props || [];
    dealsEl.innerHTML = list.slice(0, 8).map((p) => `
      <div class="card">
        <strong>${(p.title || "").slice(0, 50)}</strong>
        <div>${fmtEuro(p.price)} · ${p.living_area || "–"} m² · ${p.postal_code || ""} ${p.city || ""}</div>
        <div class="muted">${p.source} · EPC ${p.epc_label || "?"}</div>
      </div>`).join("") || "<p class='muted'>Geen real data. Run Heylen/Walls.</p>";
  } catch (e) {
    el.innerHTML = `<p class='muted'>Fout: ${e.message}</p>`;
  }
}

async function loadProperties() {
  const box = document.getElementById("props-table");
  try {
    const ex = document.getElementById("exclude-demo")?.checked ? "&exclude_demo=true" : "";
    const data = await fetchJSON(API + "/properties?limit=50" + ex);
    const list = data.items || data || [];
    box.innerHTML = `<table class="data-table"><thead><tr><th>Prijs</th><th>m²</th><th>PC</th><th>EPC</th><th>Bron</th><th>Titel</th></tr></thead><tbody>` +
      list.map((p) => `<tr><td>${fmtEuro(p.price)}</td><td>${p.living_area || "–"}</td><td>${p.postal_code || ""}</td><td>${p.epc_label || ""}</td><td>${p.source}</td><td>${(p.title || "").slice(0, 40)}</td></tr>`).join("") +
      `</tbody></table>`;
  } catch (e) {
    box.innerHTML = `<p class='muted'>${e.message}</p>`;
  }
}

async function loadDeals() {
  const box = document.getElementById("deals-list");
  try {
    const data = await fetchJSON(API + "/deals?limit=20").catch(() =>
      fetchJSON(API + "/properties?exclude_demo=true&limit=20")
    );
    const list = data.items || data.deals || data || [];
    box.innerHTML = list.slice(0, 15).map((p) => `
      <div class="card"><strong>${fmtEuro(p.price)}</strong> ${p.living_area || "–"} m²
      <div>${p.postal_code} ${(p.title || "").slice(0, 40)}</div>
      <div class="muted">${p.deal_status || p.source || ""}</div></div>`).join("") || "<p class='muted'>Geen deals</p>";
  } catch (e) {
    box.innerHTML = `<p class='muted'>${e.message}</p>`;
  }
}

async function loadSources() {
  const box = document.getElementById("sources-table");
  try {
    const data = await fetchJSON(API + "/sources");
    const list = data.sources || [];
    box.innerHTML = `<table class="data-table"><thead><tr><th>Source</th><th>Status</th><th>Method</th></tr></thead><tbody>` +
      list.map((s) => `<tr><td>${s.source}</td><td>${s.status}</td><td>${s.method}</td></tr>`).join("") +
      `</tbody></table>`;
  } catch (e) {
    box.innerHTML = `<p class='muted'>${e.message}</p>`;
  }
}

async function loadMap() {
  if (typeof L === "undefined") return;
  const mapEl = document.getElementById("map");
  if (!mapEl._leaflet) {
    const map = L.map("map").setView([51.22, 4.42], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OSM" }).addTo(map);
    mapEl._leaflet = map;
  }
  try {
    const data = await fetchJSON(API + "/map/properties?limit=200");
    const map = mapEl._leaflet;
    (data.features || []).forEach((f) => {
      L.circleMarker([f.lat, f.lng], { radius: 6 }).addTo(map)
        .bindPopup(`${f.title || ""}<br/>${fmtEuro(f.price)}`);
    });
  } catch (e) { /* ignore */ }
}

document.getElementById("btn-load-props")?.addEventListener("click", loadProperties);
document.getElementById("btn-run-heylen")?.addEventListener("click", async () => {
  const log = document.getElementById("import-log");
  log.textContent = "Running Heylen…";
  try {
    const r = await fetchJSON(API + "/sources/heylen/run?limit=600", { method: "POST" });
    log.textContent = JSON.stringify(r, null, 2);
  } catch (e) { log.textContent = e.message; }
});
document.getElementById("btn-run-walls")?.addEventListener("click", async () => {
  const log = document.getElementById("import-log");
  log.textContent = "Running Walls…";
  try {
    const r = await fetchJSON(API + "/sources/walls/run?limit=150", { method: "POST" });
    log.textContent = JSON.stringify(r, null, 2);
  } catch (e) { log.textContent = e.message; }
});

(function () {
  const input = document.getElementById("api-base-input");
  const btn = document.getElementById("api-base-save");
  if (input) input.value = localStorage.getItem("vast_api") || "http://127.0.0.1:8000/api";
  btn?.addEventListener("click", () => {
    localStorage.setItem("vast_api", (input?.value || "").trim().replace(/\/$/, ""));
    location.reload();
  });
})();

loadDashboard();
