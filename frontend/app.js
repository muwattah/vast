const API = "http://localhost:8000/api";

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function scoreClass(s) {
  if (s == null) return "low";
  if (s >= 8) return "high";
  if (s >= 6) return "mid";
  return "low";
}

function fmt(n) {
  if (n == null) return "–";
  return new Intl.NumberFormat("nl-BE", { maximumFractionDigits: 0 }).format(n);
}

function fmtEuro(n) {
  if (n == null) return "–";
  return "€" + fmt(n);
}

async function loadStats() {
  try {
    const s = await fetchJSON(`${API}/stats`);
    document.getElementById("stat-total").textContent = s.total_properties ?? "–";
    document.getElementById("stat-diy").textContent = s.diy_projects ?? "–";
    document.getElementById("stat-high").textContent = s.score_above_8 ?? "–";
    document.getElementById("stat-avg").textContent = s.avg_price_per_m2 ? "€" + fmt(s.avg_price_per_m2) : "–";
    document.getElementById("stat-margin").textContent = s.highest_estimated_margin ? fmtEuro(s.highest_estimated_margin) : "–";
  } catch (e) {
    console.error(e);
  }
}

async function loadProperties() {
  const params = new URLSearchParams();
  const minP = document.getElementById("min_price").value;
  const maxP = document.getElementById("max_price").value;
  const minA = document.getElementById("min_area").value;
  const minS = document.getElementById("min_score").value;
  if (minP) params.set("min_price", minP);
  if (maxP) params.set("max_price", maxP);
  if (minA) params.set("min_area", minA);
  if (minS) params.set("min_score", minS);
  if (document.getElementById("only_renovate").checked) params.set("only_renovate", "true");
  if (document.getElementById("only_diy").checked) params.set("only_diy", "true");
  params.set("sort", document.getElementById("sort").value);

  const tbody = document.getElementById("prop-body");
  tbody.innerHTML = "<tr><td colspan='8'>Laden…</td></tr>";
  try {
    const list = await fetchJSON(`${API}/properties?${params}`);
    document.getElementById("status-msg").textContent = `${list.length} resultaten`;
    if (!list.length) {
      tbody.innerHTML = "<tr><td colspan='8'>Geen panden gevonden</td></tr>";
      return;
    }
    tbody.innerHTML = list.map(p => `
      <tr data-id="${p.id}">
        <td><span class="score ${scoreClass(p.investment_score)}">${p.investment_score ?? "–"}</span></td>
        <td>
          <strong>${p.title.slice(0, 55)}${p.title.length > 55 ? "…" : ""}</strong><br>
          <small style="color:var(--muted)">${p.postal_code || ""} ${p.district || p.city || ""}</small>
        </td>
        <td>${fmtEuro(p.price)}</td>
        <td>${p.living_area ? p.living_area + " m²" : "–"}</td>
        <td>${p.price_per_m2 ? "€" + fmt(p.price_per_m2) : "–"}</td>
        <td class="epc">${p.epc_label || "–"}</td>
        <td>${p.estimated_profit_max ? "+" + fmtEuro(p.estimated_profit_max) : "–"}</td>
        <td><button class="btn-primary" style="padding:0.3rem 0.6rem;font-size:0.8rem" onclick="event.stopPropagation();openDetail(${p.id})">Detail</button></td>
      </tr>
    `).join("");
    tbody.querySelectorAll("tr[data-id]").forEach(tr => {
      tr.addEventListener("click", () => openDetail(tr.dataset.id));
    });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan='8'>Fout: ${e.message}. Is de backend actief op :8000?</td></tr>`;
  }
}

async function openDetail(id) {
  const modal = document.getElementById("modal");
  const body = document.getElementById("modal-body");
  body.innerHTML = "Laden…";
  modal.classList.remove("hidden");
  try {
    const p = await fetchJSON(`${API}/properties/${id}`);
    body.innerHTML = `
      <h2 style="margin-bottom:0.25rem">${p.title}</h2>
      <p style="color:var(--muted);margin-bottom:1rem">${p.address || ""} · ${p.postal_code} ${p.city || ""}</p>
      <div class="detail-grid">
        <div class="detail-item"><span>Vraagprijs</span><strong>${fmtEuro(p.price)}</strong></div>
        <div class="detail-item"><span>Oppervlakte</span><strong>${p.living_area || "–"} m²</strong></div>
        <div class="detail-item"><span>€/m²</span><strong>${p.price_per_m2 ? "€"+fmt(p.price_per_m2) : "–"}</strong></div>
        <div class="detail-item"><span>EPC</span><strong>${p.epc_label || "–"} ${p.epc_score ? "("+p.epc_score+")" : ""}</strong></div>
        <div class="detail-item"><span>Investment Score</span><strong class="${scoreClass(p.investment_score)}">${p.investment_score ?? "–"}</strong></div>
        <div class="detail-item"><span>DIY Score</span><strong>${p.diy_score ?? "–"}</strong></div>
      </div>

      <div class="section-title">Financiële analyse (indicatief)</div>
      <div class="detail-grid">
        <div class="detail-item"><span>Renovatiekost</span>${fmtEuro(p.estimated_renovation_cost_min)} – ${fmtEuro(p.estimated_renovation_cost_max)}</div>
        <div class="detail-item"><span>Waarde na renovatie</span>${fmtEuro(p.estimated_after_renovation_value_min)} – ${fmtEuro(p.estimated_after_renovation_value_max)}</div>
        <div class="detail-item"><span>Potentiële marge</span>${fmtEuro(p.estimated_profit_min)} – ${fmtEuro(p.estimated_profit_max)}</div>
        <div class="detail-item"><span>ROI</span>${p.estimated_roi_min ?? "–"}% – ${p.estimated_roi_max ?? "–"}%</div>
      </div>

      <div class="section-title">AI / Regel-analyse</div>
      <p>${p.ai_summary || "Geen samenvatting"}</p>
      <div class="section-title">Kansen</div>
      <ul>${(p.ai_opportunities || []).map(o => `<li>${o}</li>`).join("") || "<li>–</li>"}</ul>
      <div class="section-title">Risico's</div>
      <ul>${(p.ai_risks || []).map(r => `<li>${r}</li>`).join("") || "<li>–</li>"}</ul>
      <div class="section-title">DIY-werken</div>
      <ul>${(p.diy_tasks || []).map(t => `<li>${t}</li>`).join("") || "<li>–</li>"}</ul>
      <div class="section-title">Professioneel / vergunning</div>
      <ul>${(p.professional_tasks || []).map(t => `<li>${t}</li>`).join("") || "<li>–</li>"}</ul>

      <p style="margin-top:1.25rem">
        <a href="${p.url}" target="_blank" rel="noopener" class="btn-primary" style="display:inline-block;text-decoration:none">Bekijk originele advertentie</a>
      </p>
      <p style="margin-top:0.75rem;font-size:0.75rem;color:var(--muted)">
        Alle bedragen zijn indicatieve schattingen en geen financieel advies.
      </p>
    `;
  } catch (e) {
    body.innerHTML = `<p>Fout: ${e.message}</p>`;
  }
}

document.getElementById("modal-close").addEventListener("click", () => {
  document.getElementById("modal").classList.add("hidden");
});
document.getElementById("modal").addEventListener("click", (e) => {
  if (e.target.id === "modal") document.getElementById("modal").classList.add("hidden");
});

document.getElementById("btn-apply").addEventListener("click", loadProperties);
document.getElementById("btn-refresh").addEventListener("click", async () => {
  const msg = document.getElementById("status-msg");
  msg.textContent = "Refresh gestart…";
  try {
    const res = await fetch(`${API}/scrape`, { method: "POST" });
    const r = await res.json();
    msg.textContent = r.message || "Klaar (scrapers disabled)";
  } catch (err) {
    msg.textContent = "Refresh: " + err.message;
  }
  loadStats();
  loadProperties();
});

loadStats();
loadProperties();
