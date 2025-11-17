# UI Manus Task — Global Layout Refinement (Spacing + Breakpoints)

This file defines the next blueprint tasks Codex must execute.

Tasks to execute now:
1. Aplicar spacing global
2. Ajustar responsividade (breakpoints Manus)

Reference files:
- STRATEGY_PROMPT.md
- docs/STRATEGY_UI.md
- docs/ui-blueprint.md
- docs/state-ui-manus.md

---

## 1. theme.css updates

Create or ensure the following variables are present:

Breakpoints:
  --ketter-breakpoint-xl
  --ketter-breakpoint-lg
  --ketter-breakpoint-md
  --ketter-breakpoint-sm

Spacing tokens:
  var(--ketter-space-xs)
  var(--ketter-space-sm)
  var(--ketter-space-md)
  var(--ketter-space-lg)
  var(--ketter-space-xl)
  var(--ketter-space-xxl)
  var(--ketter-space-xxxl)

Apply these tokens consistently across layout, containers and page shells.

---

## 2. App.css updates

Apply global spacing using the tokens above.

Normalize spacing across:
- sections
- cards
- headers
- charts
- grids
- logs
- KPI blocks

Ensure:
- .ui-container uses breakpoint tokens
- responsive rules stack gracefully at lg, md, sm
- remove all remaining hardcoded px/rem and replace with tokens

---

## 3. Page Layout Pass

Update layout wrappers in these files:
- frontend/src/pages/DashboardPage.jsx
- frontend/src/pages/TransfersPage.jsx
- frontend/src/pages/AuditPage.jsx
- frontend/src/pages/SystemHealthPage.jsx
- frontend/src/pages/SettingsPage.jsx

Requirements:
- Use .ui-container
- Apply tokenized padding/margin/gaps
- Unify spacing hierarchy across all pages

---

## 4. Documentation Update (docs/state-ui-manus.md)

Mark these tasks complete:
- Aplicar spacing global
- Ajustar responsividade (breakpoints Manus)

Append:
- PATCH GLOBAL SPACING MANUS
- PATCH BREAKPOINTS MANUS

Summaries must describe the theme/css/layout adjustments.

---

## 5. Commit

Stage all modified files and commit with:

feat(ui-manus): global spacing + breakpoint refinement

The commit must be executed automatically.

Do not provide commentary.
Perform all actions directly.

