# UI Manus Task — TransfersPage Refinement

This file defines the next blueprint actions Codex must execute for the Transfers page.

Tasks:
1. Aplicar o layout Manus
2. Ajustar TransferCard
3. Ajustar TransferDetailsPanel
4. Refinar tabela / grid de jobs
5. Ajustar cores e severidades

Reference files:
- STRATEGY_PROMPT.md
- docs/STRATEGY_UI.md
- docs/ui-blueprint.md
- docs/state-ui-manus.md

---

## 1. TransfersPage Layout

- Wrap page using `.ui-container`
- Apply spacing tokens (padding/gaps)
- Apply Manus radius/shadow/transition tokens
- Improve section hierarchy (title → queue → details panel)

Files:
- frontend/src/pages/TransfersPage.jsx
- App.css

---

## 2. TransferCard Refinement

- Normalize spacing and padding
- Use radius/shadow tokens
- Typography tokens for filename/source/destination/status
- Severity colors using gray + primary Manus palette
- Responsive stacking for md/sm breakpoints

Files:
- frontend/src/components/TransferCard.jsx
- App.css

---

## 3. TransferDetailsPanel

- Apply Manus spacing and radius
- Improve heading hierarchy
- Align all fields using spacing tokens
- Apply typography scale to labels and values
- Ensure responsive layout

Files:
- frontend/src/components/TransferDetailsPanel.jsx
- App.css

---

## 4. Queue Grid / Jobs Table

- Apply spacing tokens
- Ensure grid collapses at md/sm
- Normalize headers and cell spacing
- Apply tokenized colors for states (pending, running, failed, completed)

Files:
- TransfersPage.jsx
- App.css

---

## 5. Documentation

Update docs/state-ui-manus.md:
- Mark Transfers tasks as complete
- Add “PATCH TRANSFERS MANUS” summary

---

## 6. Commit

feat(ui-manus): transfers page refinement

Do not provide commentary.
Perform all actions directly.

