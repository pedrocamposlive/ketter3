# UI Manus Task — Dashboard Refinement

This file defines the next blueprint tasks Codex must execute.

Tasks to execute now (Dashboard section):
1. Ajustar KPIs para estilo Manus
2. Refinar Throughput Chart
3. Refinar Donut Chart
4. Refinar Status Grid
5. Refinar Alerts Panel (SIEM Manus)
6. Implementar hierarchy spacing Manus
7. Polir tipografia das seções

Reference files:
- STRATEGY_PROMPT.md
- docs/STRATEGY_UI.md
- docs/ui-blueprint.md
- docs/state-ui-manus.md

---

## 1. KPI Card Refinement

Update KPI components:
- Apply spacing tokens for padding, margin, gaps
- Apply radius/shadow/transition tokens
- Apply typography tokens
- Ensure the KPI card grid uses responsive Manus breakpoints
- Replace any remaining hardcoded values

Files:
- frontend/src/components/KpiCard.jsx
- frontend/src/pages/DashboardPage.jsx
- App.css

---

## 2. Throughput Chart Refinement

Update:
- spacing
- stroke widths
- hover effects
- legend spacing
- responsive stacking at md/sm

Files:
- frontend/src/components/ThroughputChart.jsx
- frontend/src/pages/DashboardPage.jsx
- App.css

---

## 3. Donut Chart Refinement

Refine donut:
- spacing tokens
- legend layout
- typography hierarchy
- responsive stacking

Files:
- frontend/src/components/MoveCopyDonut.jsx
- DashboardPage.jsx
- App.css

---

## 4. Status Grid Refinement

- Normalize spacing
- Apply radius/shadow/tokens
- Improve item hierarchy
- Responsive stacking at md/sm

Files:
- frontend/src/layout/Layout.jsx
- frontend/src/pages/DashboardPage.jsx
- App.css

---

## 5. Alerts Panel (SIEM Manus)

- Apply Manus spacing
- Typography polish
- Shadow/radius/transition tokens
- Improve severity badges

Files:
- frontend/src/components/AlertsPanel.jsx
- App.css

---

## 6. Dashboard Hierarchy Pass

Apply consistent section spacing:  
title → block → charts → status → alerts → logs

Ensure all use spacing tokens and responsive breakpoints.

---

## 7. Documentation

Update docs/state-ui-manus.md:
- Mark all tasks above as complete
- Add PATCH DASHBOARD MANUS describing refinements

---

## 8. Commit

Commit message:

feat(ui-manus): dashboard refinement

Do not provide commentary.
Perform all actions directly.

