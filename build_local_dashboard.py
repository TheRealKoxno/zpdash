#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path


OUT_DIR = Path("/Users/ilyazenno/Desktop/zp_dumper/dashboard_output")
OUT_FILE = OUT_DIR / "dashboard.html"


HTML_TEMPLATE = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ZennoPoster Local Dashboard</title>
  <style>
    :root {
      --bg: #0b1020;
      --panel: #121a31;
      --panel-2: #182242;
      --text: #e8eeff;
      --muted: #9aa8d1;
      --accent: #4ad2ff;
      --accent-2: #69f0ae;
      --warn: #ffd166;
      --danger: #ff6b6b;
      --line: #25315f;
      --chip: #1f2d57;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: radial-gradient(circle at 15% 20%, #1a2650 0, var(--bg) 48%), var(--bg);
      color: var(--text);
      font-family: "Segoe UI", Tahoma, sans-serif;
      line-height: 1.4;
    }
    .container {
      max-width: 1480px;
      margin: 0 auto;
      padding: 18px;
    }
    h1 {
      margin: 0 0 6px 0;
      font-size: 26px;
    }
    .subtitle {
      color: var(--muted);
      margin-bottom: 14px;
      font-size: 14px;
    }
    .card-grid {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      margin-bottom: 14px;
    }
    .card {
      background: linear-gradient(180deg, var(--panel) 0%, #0f1730 100%);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      min-height: 88px;
    }
    .card .k { color: var(--muted); font-size: 12px; }
    .card .v { font-size: 24px; font-weight: 700; margin-top: 6px; }
    .tabs {
      display: flex;
      gap: 6px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }
    .tab-btn {
      border: 1px solid var(--line);
      background: var(--panel-2);
      color: var(--text);
      border-radius: 10px;
      padding: 8px 12px;
      cursor: pointer;
      font-size: 13px;
    }
    .tab-btn.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px var(--accent) inset;
    }
    .tab {
      display: none;
      animation: fadeIn 160ms ease-out;
    }
    .tab.active { display: block; }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .panel {
      background: linear-gradient(180deg, var(--panel) 0%, #0f1730 100%);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      margin-bottom: 12px;
    }
    .panel h2 {
      margin: 0 0 10px 0;
      font-size: 16px;
    }
    .row {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(12, 1fr);
    }
    .col-6 { grid-column: span 6; }
    .col-4 { grid-column: span 4; }
    .col-12 { grid-column: span 12; }
    @media (max-width: 980px) {
      .col-6, .col-4 { grid-column: span 12; }
    }
    .filter-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 8px;
      margin-bottom: 10px;
    }
    label {
      font-size: 12px;
      color: var(--muted);
      display: block;
      margin-bottom: 4px;
    }
    input, select {
      width: 100%;
      border: 1px solid var(--line);
      background: #0e1630;
      color: var(--text);
      border-radius: 8px;
      padding: 7px 8px;
      font-size: 13px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    th, td {
      text-align: left;
      padding: 7px 6px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }
    th {
      color: var(--muted);
      font-weight: 600;
      position: sticky;
      top: 0;
      background: #111a34;
      z-index: 1;
    }
    .table-wrap {
      max-height: 520px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 10px;
    }
    .chip {
      display: inline-block;
      background: var(--chip);
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 11px;
      margin-right: 4px;
      margin-bottom: 3px;
    }
    .bar-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }
    .bar-label {
      width: 180px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 12px;
      color: #d9e4ff;
    }
    .bar {
      height: 14px;
      border-radius: 7px;
      background: linear-gradient(90deg, var(--accent), #84e0ff);
      min-width: 2px;
    }
    .bar2 {
      background: linear-gradient(90deg, var(--accent-2), #8ef8b8);
    }
    .bar-value {
      width: 54px;
      text-align: right;
      color: var(--muted);
      font-size: 12px;
    }
    .muted { color: var(--muted); }
    .danger { color: var(--danger); }
    .warn { color: var(--warn); }
    .ok { color: var(--accent-2); }
    .mini {
      font-size: 11px;
      color: var(--muted);
    }
    .top-links a {
      color: var(--accent);
      text-decoration: none;
      margin-right: 10px;
      font-size: 12px;
    }
    .sticky-actions {
      position: sticky;
      top: 0;
      z-index: 2;
      padding-bottom: 8px;
      background: linear-gradient(180deg, rgba(11,16,32,0.96) 0%, rgba(11,16,32,0.65) 80%, rgba(11,16,32,0) 100%);
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="sticky-actions">
      <h1>ZennoPoster Local Dashboard</h1>
      <div class="subtitle">Интерактивный просмотр выгрузки 16-24 Feb 2026 • Сгенерировано: __GENERATED_AT__</div>
      <div class="top-links">
        <a href="dashboard_report.md" target="_blank">dashboard_report.md</a>
        <a href="users_profile_dashboard.csv" target="_blank">users_profile_dashboard.csv</a>
        <a href="projects_detailed_dashboard.csv" target="_blank">projects_detailed_dashboard.csv</a>
      </div>
    </div>

    <div class="card-grid" id="summaryCards"></div>

    <div class="tabs">
      <button class="tab-btn active" data-tab="overview">Обзор</button>
      <button class="tab-btn" data-tab="users">Пользователи</button>
      <button class="tab-btn" data-tab="projects">Проекты</button>
      <button class="tab-btn" data-tab="errors">Ошибки</button>
    </div>

    <section class="tab active" id="tab-overview">
      <div class="panel">
        <h2>Фильтр обзора</h2>
        <div class="filter-grid">
          <div>
            <label for="ovPlan">Lite/Pro</label>
            <select id="ovPlan">
              <option value="all">all</option>
              <option value="lite">lite</option>
              <option value="pro">pro</option>
            </select>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col-6 panel">
          <h2>Топ сайтов (по пользователям)</h2>
          <div id="topSitesBars"></div>
        </div>
        <div class="col-6 panel">
          <h2>Топ тем (по пользователям)</h2>
          <div id="topThemesBars"></div>
        </div>
        <div class="col-12 panel">
          <h2>Сайты: users vs projects</h2>
          <div class="table-wrap">
            <table id="topSitesTable"></table>
          </div>
        </div>
      </div>
    </section>

    <section class="tab" id="tab-users">
      <div class="panel">
        <h2>Фильтры пользователей</h2>
        <div class="filter-grid">
          <div>
            <label for="uSearch">GUID / сайты / темы</label>
            <input id="uSearch" placeholder="поиск..." />
          </div>
          <div>
            <label for="uLevel">Уровень</label>
            <select id="uLevel"></select>
          </div>
          <div>
            <label for="uPlan">Lite/Pro</label>
            <select id="uPlan"></select>
          </div>
          <div>
            <label for="uLeft">Ушел >1 дня</label>
            <select id="uLeft">
              <option value="all">all</option>
              <option value="yes">yes</option>
              <option value="no">no</option>
            </select>
          </div>
          <div>
            <label for="uMinProjects">Мин. проектов</label>
            <input id="uMinProjects" type="number" min="0" value="0" />
          </div>
          <div>
            <label for="uLimit">Показать строк</label>
            <input id="uLimit" type="number" min="20" max="1000" value="300" />
          </div>
        </div>
        <div class="mini" id="usersInfo"></div>
      </div>
      <div class="panel">
        <h2>Таблица пользователей</h2>
        <div class="table-wrap">
          <table id="usersTable"></table>
        </div>
      </div>
    </section>

    <section class="tab" id="tab-projects">
      <div class="panel">
        <h2>Фильтры проектов</h2>
        <div class="filter-grid">
          <div>
            <label for="pGuid">GUID</label>
            <input id="pGuid" placeholder="starts with / contains" />
          </div>
          <div>
            <label for="pTheme">Тема</label>
            <select id="pTheme"></select>
          </div>
          <div>
            <label for="pPlan">Lite/Pro</label>
            <select id="pPlan"></select>
          </div>
          <div>
            <label for="pDomain">Домен содержит</label>
            <input id="pDomain" placeholder="google.com" />
          </div>
          <div>
            <label for="pOnlyErr">Только с ошибками</label>
            <select id="pOnlyErr">
              <option value="all">all</option>
              <option value="yes">yes</option>
              <option value="no">no</option>
            </select>
          </div>
          <div>
            <label for="pLimit">Показать строк</label>
            <input id="pLimit" type="number" min="50" max="2000" value="400" />
          </div>
        </div>
        <div class="mini" id="projectsInfo"></div>
      </div>
      <div class="panel">
        <h2>Таблица проектов</h2>
        <div class="table-wrap">
          <table id="projectsTable"></table>
        </div>
      </div>
    </section>

    <section class="tab" id="tab-errors">
      <div class="row">
        <div class="col-12 panel">
          <h2>Фильтр ошибок</h2>
          <div class="filter-grid">
            <div>
              <label for="ePlan">Lite/Pro</label>
              <select id="ePlan"></select>
            </div>
          </div>
        </div>
        <div class="col-6 panel">
          <h2>Топ частых ошибок</h2>
          <div id="topErrorsBars"></div>
        </div>
        <div class="col-6 panel">
          <h2>Топ последних ошибок пользователей</h2>
          <div id="lastErrorsBars"></div>
        </div>
        <div class="col-12 panel">
          <h2>Ошибки по уровню пользователя</h2>
          <div class="filter-grid">
            <div>
              <label for="errLevel">Уровень</label>
              <select id="errLevel"></select>
            </div>
          </div>
          <div class="row">
            <div class="col-6">
              <div class="mini" style="margin-bottom:6px;">Частые ошибки в уровне</div>
              <div id="errorsByLevelBars"></div>
            </div>
            <div class="col-6">
              <div class="mini" style="margin-bottom:6px;">Последние ошибки в уровне</div>
              <div id="lastErrorsByLevelBars"></div>
            </div>
            <div class="col-12" style="margin-top:8px;">
              <div class="table-wrap">
                <table id="errorsByLevelTable"></table>
              </div>
            </div>
          </div>
        </div>
        <div class="col-12 panel">
          <h2>Детали ошибок</h2>
          <div class="table-wrap">
            <table id="errorsTable"></table>
          </div>
        </div>
      </div>
    </section>
  </div>

  <script>
    const DATA_FILES = {
      sites: "dashboard_top_sites.csv",
      themes: "dashboard_top_themes.csv",
      errors: "dashboard_top_errors.csv",
      lastErrors: "dashboard_last_errors.csv",
      errorsByLevel: "dashboard_errors_by_level.csv",
      lastErrorsByLevel: "dashboard_last_errors_by_level.csv",
      errorsByPlan: "dashboard_errors_by_plan.csv",
      lastErrorsByPlan: "dashboard_last_errors_by_plan.csv",
      users: "users_profile_dashboard.csv",
      projects: "projects_detailed_dashboard.csv"
    };

    function parseCSV(text) {
      const rows = [];
      let row = [];
      let field = "";
      let i = 0;
      let inQuotes = false;
      while (i < text.length) {
        const ch = text[i];
        if (inQuotes) {
          if (ch === '"') {
            if (text[i + 1] === '"') {
              field += '"';
              i += 1;
            } else {
              inQuotes = false;
            }
          } else {
            field += ch;
          }
        } else {
          if (ch === '"') {
            inQuotes = true;
          } else if (ch === ",") {
            row.push(field);
            field = "";
          } else if (ch === "\\n") {
            row.push(field);
            rows.push(row);
            row = [];
            field = "";
          } else if (ch === "\\r") {
          } else {
            field += ch;
          }
        }
        i += 1;
      }
      if (field.length || row.length) {
        row.push(field);
        rows.push(row);
      }
      if (!rows.length) return [];
      const headers = rows[0].map((h, idx) => (idx === 0 ? h.replace(/^\\uFEFF/, "") : h));
      const out = [];
      for (let r = 1; r < rows.length; r += 1) {
        if (rows[r].length === 1 && rows[r][0] === "") continue;
        const obj = {};
        for (let c = 0; c < headers.length; c += 1) {
          obj[headers[c]] = rows[r][c] ?? "";
        }
        out.push(obj);
      }
      return out;
    }

    function asInt(v) {
      const n = parseInt(String(v || "").replace(/[^0-9-]/g, ""), 10);
      return Number.isFinite(n) ? n : 0;
    }

    function asFloat(v) {
      const n = parseFloat(String(v || "").replace(",", "."));
      return Number.isFinite(n) ? n : 0;
    }

    function splitList(value) {
      return String(value || "")
        .split(",")
        .map(v => v.trim())
        .filter(Boolean);
    }

    function renderTable(tableId, rows, columns) {
      const table = document.getElementById(tableId);
      if (!table) return;
      const head = "<thead><tr>" + columns.map(c => `<th>${c.label}</th>`).join("") + "</tr></thead>";
      const bodyRows = rows.map(row => {
        const cells = columns.map(c => `<td>${escapeHtml(c.render ? c.render(row[c.key], row) : row[c.key])}</td>`).join("");
        return "<tr>" + cells + "</tr>";
      }).join("");
      table.innerHTML = head + "<tbody>" + bodyRows + "</tbody>";
    }

    function escapeHtml(raw) {
      return String(raw ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }

    function uniqueValues(rows, key) {
      const set = new Set();
      rows.forEach(r => {
        const v = (r[key] || "").trim();
        if (v) set.add(v);
      });
      return Array.from(set).sort((a, b) => a.localeCompare(b, "ru"));
    }

    function fillSelect(selectId, values, withAll = true) {
      const el = document.getElementById(selectId);
      if (!el) return;
      const opts = [];
      if (withAll) opts.push(`<option value="all">all</option>`);
      values.forEach(v => opts.push(`<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`));
      el.innerHTML = opts.join("");
    }

    function computeOverviewFromProjects(projects, plan) {
      const domainMap = new Map();
      const themeMap = new Map();
      const filtered = projects.filter(p => {
        if (plan === "all") return true;
        return (p.variant || "").toLowerCase() === plan;
      });

      filtered.forEach(p => {
        const guid = p.guid || "";
        const domains = splitList(p.domains);
        const ops = splitList(p.operations);
        const theme = p.theme || "";

        domains.forEach(domain => {
          if (!domainMap.has(domain)) {
            domainMap.set(domain, { users: new Set(), projects: 0, ops: new Map(), themes: new Map() });
          }
          const item = domainMap.get(domain);
          item.users.add(guid);
          item.projects += 1;
          ops.forEach(op => item.ops.set(op, (item.ops.get(op) || 0) + 1));
          if (theme) item.themes.set(theme, (item.themes.get(theme) || 0) + 1);
        });

        if (theme) {
          if (!themeMap.has(theme)) {
            themeMap.set(theme, { users: new Set(), projects: 0, ops: new Map() });
          }
          const t = themeMap.get(theme);
          t.users.add(guid);
          t.projects += 1;
          ops.forEach(op => t.ops.set(op, (t.ops.get(op) || 0) + 1));
        }
      });

      const toTopList = mapObj => Array.from(mapObj.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([k]) => k)
        .join(", ");

      const siteRows = Array.from(domainMap.entries()).map(([domain, item]) => ({
        domain,
        users_count: item.users.size,
        projects_count: item.projects,
        what_users_do: toTopList(item.ops),
        top_themes: toTopList(item.themes)
      })).sort((a, b) => {
        if (asInt(b.users_count) !== asInt(a.users_count)) return asInt(b.users_count) - asInt(a.users_count);
        return asInt(b.projects_count) - asInt(a.projects_count);
      });

      const themeRows = Array.from(themeMap.entries()).map(([theme, item]) => ({
        theme,
        users_count: item.users.size,
        projects_count: item.projects,
        typical_actions: toTopList(item.ops)
      })).sort((a, b) => {
        if (asInt(b.users_count) !== asInt(a.users_count)) return asInt(b.users_count) - asInt(a.users_count);
        return asInt(b.projects_count) - asInt(a.projects_count);
      });

      return { siteRows, themeRows };
    }

    function renderBars(containerId, rows, labelKey, valueKey, limit = 15, colorClass = "") {
      const root = document.getElementById(containerId);
      if (!root) return;
      const data = rows.slice(0, limit);
      const max = Math.max(1, ...data.map(r => asInt(r[valueKey])));
      root.innerHTML = data.map(r => {
        const v = asInt(r[valueKey]);
        const width = Math.max(2, Math.round((v / max) * 100));
        return `
          <div class="bar-wrap">
            <div class="bar-label" title="${escapeHtml(r[labelKey])}">${escapeHtml(r[labelKey])}</div>
            <div style="flex:1; background:#0d1631; border:1px solid var(--line); border-radius:8px; padding:1px;">
              <div class="bar ${colorClass}" style="width:${width}%"></div>
            </div>
            <div class="bar-value">${v}</div>
          </div>
        `;
      }).join("");
    }

    function statCards(users, projects) {
      const totalUsers = users.length;
      const totalProjects = projects.length;
      const left = users.filter(u => (u.left_more_than_1_day || "").toLowerCase() === "yes").length;
      const active = totalUsers - left;
      const pro = users.filter(u => (u.lite_or_pro || "").toLowerCase() === "pro").length;
      const lite = users.filter(u => (u.lite_or_pro || "").toLowerCase() === "lite").length;
      const avgProjects = totalUsers ? (totalProjects / totalUsers).toFixed(1) : "0";

      const cards = [
        ["GUID пользователей", totalUsers],
        ["Проектов", totalProjects],
        ["Среднее проектов/польз.", avgProjects],
        ["Lite", lite],
        ["Pro", pro],
        ["Ушли >1 дня", left],
        ["Активны <=1 дня", active],
      ];
      const root = document.getElementById("summaryCards");
      root.innerHTML = cards.map(([k, v]) => `<div class="card"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");
    }

    function initTabs() {
      const btns = Array.from(document.querySelectorAll(".tab-btn"));
      btns.forEach(btn => {
        btn.addEventListener("click", () => {
          btns.forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
          const name = btn.getAttribute("data-tab");
          Array.from(document.querySelectorAll(".tab")).forEach(t => t.classList.remove("active"));
          document.getElementById("tab-" + name).classList.add("active");
        });
      });
    }

    async function loadAll() {
      const entries = Object.entries(DATA_FILES);
      const result = {};
      for (const [k, file] of entries) {
        const res = await fetch(file);
        if (!res.ok) throw new Error(`Не удалось загрузить ${file}`);
        result[k] = parseCSV(await res.text());
      }
      return result;
    }

    function wireUsers(users) {
      fillSelect("uLevel", uniqueValues(users, "level"));
      fillSelect("uPlan", uniqueValues(users, "lite_or_pro"));
      const controls = ["uSearch", "uLevel", "uPlan", "uLeft", "uMinProjects", "uLimit"];
      controls.forEach(id => document.getElementById(id).addEventListener("input", render));
      controls.forEach(id => document.getElementById(id).addEventListener("change", render));

      function render() {
        const q = (document.getElementById("uSearch").value || "").toLowerCase().trim();
        const level = document.getElementById("uLevel").value;
        const plan = document.getElementById("uPlan").value;
        const left = document.getElementById("uLeft").value;
        const minProjects = asInt(document.getElementById("uMinProjects").value);
        const limit = Math.max(20, asInt(document.getElementById("uLimit").value || "300"));

        let filtered = users.filter(u => {
          if (level !== "all" && (u.level || "") !== level) return false;
          if (plan !== "all" && (u.lite_or_pro || "") !== plan) return false;
          if (left !== "all" && (u.left_more_than_1_day || "") !== left) return false;
          if (asInt(u.projects_count) < minProjects) return false;
          if (q) {
            const hay = [
              u.guid, u.top_sites, u.top_themes, u.main_operations,
              u.stop_points, u.last_error_category, u.characteristic
            ].join(" ").toLowerCase();
            if (!hay.includes(q)) return false;
          }
          return true;
        });

        filtered.sort((a, b) => asInt(b.projects_count) - asInt(a.projects_count));
        const total = filtered.length;
        filtered = filtered.slice(0, limit);
        document.getElementById("usersInfo").innerHTML =
          `Найдено: <b>${total}</b> • Показано: <b>${filtered.length}</b>`;

        renderTable("usersTable", filtered, [
          { key: "guid", label: "GUID" },
          { key: "lite_or_pro", label: "Lite/Pro" },
          { key: "projects_count", label: "Проекты" },
          { key: "level", label: "Уровень" },
          { key: "confidence_pct", label: "Уверенность %" },
          { key: "left_more_than_1_day", label: "Ушел >1д" },
          { key: "top_sites", label: "Топ сайты" },
          { key: "top_themes", label: "Топ темы" },
          { key: "stop_points", label: "Где стопорится" },
          { key: "last_error_category", label: "Последняя ошибка" },
          { key: "characteristic", label: "Характеристика" }
        ]);
      }

      render();
    }

    function wireProjects(projects) {
      fillSelect("pTheme", uniqueValues(projects, "theme"));
      fillSelect("pPlan", uniqueValues(projects, "variant"));
      const controls = ["pGuid", "pTheme", "pPlan", "pDomain", "pOnlyErr", "pLimit"];
      controls.forEach(id => document.getElementById(id).addEventListener("input", render));
      controls.forEach(id => document.getElementById(id).addEventListener("change", render));

      function render() {
        const guidQ = (document.getElementById("pGuid").value || "").toLowerCase().trim();
        const theme = document.getElementById("pTheme").value;
        const plan = document.getElementById("pPlan").value;
        const domainQ = (document.getElementById("pDomain").value || "").toLowerCase().trim();
        const onlyErr = document.getElementById("pOnlyErr").value;
        const limit = Math.max(50, asInt(document.getElementById("pLimit").value || "400"));

        let filtered = projects.filter(p => {
          if (theme !== "all" && (p.theme || "") !== theme) return false;
          if (plan !== "all" && (p.variant || "") !== plan) return false;
          if (guidQ && !(p.guid || "").toLowerCase().includes(guidQ)) return false;
          if (domainQ && !(p.domains || "").toLowerCase().includes(domainQ)) return false;
          const errCount = asInt(p.errors_count);
          if (onlyErr === "yes" && errCount <= 0) return false;
          if (onlyErr === "no" && errCount > 0) return false;
          return true;
        });

        filtered.sort((a, b) => asInt(b.project_number) - asInt(a.project_number));
        const total = filtered.length;
        filtered = filtered.slice(0, limit);
        document.getElementById("projectsInfo").innerHTML =
          `Найдено: <b>${total}</b> • Показано: <b>${filtered.length}</b>`;

        renderTable("projectsTable", filtered, [
          { key: "guid", label: "GUID" },
          { key: "session", label: "Сессия" },
          { key: "project_file", label: "Проект" },
          { key: "project_time", label: "Время" },
          { key: "theme", label: "Тема" },
          { key: "domains", label: "Домены" },
          { key: "operations", label: "Действия" },
          { key: "edit_versions", label: "Версий" },
          { key: "errors_count", label: "Ошибок" },
          { key: "last_error_category", label: "Последняя ошибка" }
        ]);
      }

      render();
    }

    function renderOverview(sites, themes, projects) {
      const planEl = document.getElementById("ovPlan");
      const render = () => {
        const plan = planEl.value || "all";
        let topSites;
        let topThemes;
        if (plan === "all") {
          topSites = [...sites].sort((a, b) => asInt(b.users_count) - asInt(a.users_count));
          topThemes = [...themes].sort((a, b) => asInt(b.users_count) - asInt(a.users_count));
        } else {
          const agg = computeOverviewFromProjects(projects, plan);
          topSites = agg.siteRows;
          topThemes = agg.themeRows;
        }
        renderBars("topSitesBars", topSites, "domain", "users_count", 16);
        renderBars("topThemesBars", topThemes, "theme", "users_count", 16, "bar2");
        renderTable("topSitesTable", topSites.slice(0, 120), [
          { key: "domain", label: "Сайт" },
          { key: "users_count", label: "Пользователи" },
          { key: "projects_count", label: "Проекты" },
          { key: "what_users_do", label: "Что делают" },
          { key: "top_themes", label: "Топ темы" }
        ]);
      };
      planEl.addEventListener("input", render);
      planEl.addEventListener("change", render);
      render();
    }

    function renderErrors(
      errors, lastErrors, errorsByLevel, lastErrorsByLevel, errorsByPlan, lastErrorsByPlan
    ) {
      fillSelect("ePlan", uniqueValues(errorsByPlan, "lite_or_pro"));
      const planEl = document.getElementById("ePlan");
      const renderMain = () => {
        const plan = planEl.value || "all";
        let topErrors;
        let topLast;
        if (plan === "all") {
          topErrors = [...errors].sort((a, b) => asInt(b.events_count) - asInt(a.events_count));
          topLast = [...lastErrors].sort((a, b) => asInt(b.users_count) - asInt(a.users_count));
        } else {
          topErrors = errorsByPlan
            .filter(r => (r.lite_or_pro || "") === plan)
            .sort((a, b) => asInt(b.events_count) - asInt(a.events_count));
          topLast = lastErrorsByPlan
            .filter(r => (r.lite_or_pro || "") === plan)
            .sort((a, b) => asInt(b.users_count) - asInt(a.users_count));
        }
        renderBars("topErrorsBars", topErrors, "error_category", "events_count", 16);
        renderBars("lastErrorsBars", topLast, "last_error_category", "users_count", 16, "bar2");
        renderTable("errorsTable", topErrors.slice(0, 150), [
          { key: "error_category", label: "Ошибка" },
          { key: "events_count", label: "Событий" },
          { key: "users_count", label: "Пользователи" },
          { key: "example_message", label: "Пример" }
        ]);
      };
      planEl.addEventListener("input", renderMain);
      planEl.addEventListener("change", renderMain);
      renderMain();

      fillSelect("errLevel", uniqueValues(errorsByLevel, "level"));
      const levelEl = document.getElementById("errLevel");
      const renderByLevel = () => {
        const level = levelEl.value || "all";
        let freq = errorsByLevel;
        let latest = lastErrorsByLevel;
        if (level !== "all") {
          freq = freq.filter(r => (r.level || "") === level);
          latest = latest.filter(r => (r.level || "") === level);
        }
        freq = [...freq].sort((a, b) => asInt(b.events_count) - asInt(a.events_count));
        latest = [...latest].sort((a, b) => asInt(b.users_count) - asInt(a.users_count));
        renderBars("errorsByLevelBars", freq, "error_category", "events_count", 14);
        renderBars("lastErrorsByLevelBars", latest, "last_error_category", "users_count", 14, "bar2");
        renderTable("errorsByLevelTable", freq.slice(0, 120), [
          { key: "level", label: "Уровень" },
          { key: "error_category", label: "Ошибка" },
          { key: "events_count", label: "Событий" },
          { key: "users_count", label: "Пользователи" }
        ]);
      };
      levelEl.addEventListener("input", renderByLevel);
      levelEl.addEventListener("change", renderByLevel);
      renderByLevel();
    }

    async function init() {
      initTabs();
      try {
        const data = await loadAll();
        statCards(data.users, data.projects);
        renderOverview(data.sites, data.themes, data.projects);
        wireUsers(data.users);
        wireProjects(data.projects);
        renderErrors(
          data.errors,
          data.lastErrors,
          data.errorsByLevel,
          data.lastErrorsByLevel,
          data.errorsByPlan,
          data.lastErrorsByPlan
        );
      } catch (err) {
        document.body.innerHTML = `<div class="container"><div class="panel"><h2>Ошибка загрузки</h2><div class="danger">${escapeHtml(err.message || String(err))}</div><p class="mini">Запустите локальный сервер в папке dashboard_output и откройте dashboard.html через http://127.0.0.1:PORT/dashboard.html</p></div></div>`;
      }
    }

    init();
  </script>
</body>
</html>
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = HTML_TEMPLATE.replace("__GENERATED_AT__", generated_at)
    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"Created: {OUT_FILE}")


if __name__ == "__main__":
    main()
