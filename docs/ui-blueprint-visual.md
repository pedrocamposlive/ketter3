# Ketter 3.0 — UI Blueprint Visual
Versão: 1.0

---

## Objetivo
Transformar a especificação visual (ui-visual-spec.md) em código React funcional,
componentizado e integrado ao backend.

---

# 1. Theme System
- Criar o arquivo: frontend/src/theme/tokens.js
- Criar o arquivo: frontend/src/theme/theme.css
- Implementar:
  - Paleta
  - Tipografia
  - Shadows
  - Borders
  - Layout grid
  - Color roles (primary, card, border, text)

---

# 2. Componentes Fundamentais

## 2.1 KPI Card
- Arquivo: frontend/src/components/KpiCard.jsx
- Props:
  - title
  - value
  - status
  - miniGraphData?

## 2.2 Alerts SIEM Panel
- Arquivo: AlertsPanel.jsx
- Lista vertical
- Badge color by severity

## 2.3 LogTimeline
- Arquivo: LogTimeline.jsx
- Linha vertical
- Marcadores
- Descrição + timestamp

## 2.4 VLANMap
- Arquivo: VLANMap.jsx
- Quatro blocos + flechas

## 2.5 Charts
Usar Recharts.

Criar:
- ThroughputChart.jsx
- MoveCopyDonut.jsx

---

# 3. Pages

## 3.1 DashboardPage
Adicionar:
- KPI Cards
- Gráfico throughput
- Donut
- Painel SIEM
- Row de indicadores

## 3.2 VLANsPage
Adicionar:
- Componente VLANMap

## 3.3 AuditPage
Adicionar:
- Timeline Forensic

## 3.4 TransferDetailsPage
Adicionar:
- Card com hashes
- Logs
- PDF button

## 3.5 SettingsPage
Adicionar:
- Fieldsets
- Switches
- Dropdowns

---

# 4. Layout Global
Alterar Layout.jsx:
- Header corporativo
- Sidebar refinada
- Espaçamentos enterprise
- Breadcrumb opcional

---

# 5. Integração com backend
Todas as rotas usam secureFetch
Mock fallback permanece habilitado.

---

# 6. Checklist de Conclusão
- Tema aplicável globalmente
- Dashboard atualizado
- VLAN Map funcionando
- Charts operacionais
- Timeline operacional
- Settings refinados
- Todos os componentes commitados

---

# 7. Entrega Final
- Commit final
- npm run build validado
- Arquivo docs/state-ui-visual.md atualizado

