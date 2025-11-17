# UI_RELEASE_FINAL_PLAN.md
Ketter 3.0 — Final UI Release Plan
Status: Preparação para entrega final

Objetivo
--------
Concluir a entrega oficial da UI do Ketter 3.0 após a execução do
API_REPAIR_JOB_AGGRESSIVE.md.

Escopo
------
Este plano cobre:

1. Build final da UI
2. Exportação de screenshots Manus UI
3. Atualização do README com seção de Release
4. Validação final e homologação

---

## 1. Final Build & Smoke Validation
[ ] Rodar “npm install” no frontend/
[ ] Rodar “npm run build” no frontend/
[ ] Confirmar que dist/ foi gerado sem erros
[ ] Rodar “uvicorn app.main:app --reload”
[ ] Abrir http://localhost:3001 (Vite dev) ou http://localhost:8000 (FastAPI static)
[ ] Executar todos os itens do SMOKE_TEST_UI.md

---

## 2. Exportação de Screenshots Oficiais
[ ] Dashboard – versão desktop
[ ] Transfers – versão desktop
[ ] Audit Page – desktop
[ ] System Health – desktop
[ ] Settings – desktop

Salvar em:
public/assets/release/ui/

E criar:
public/assets/release/ui/manifest.json  
contendo a lista de imagens.

---

## 3. Atualizar README.md (Seção de Release)
[ ] Criar seção “Ketter 3.0 — UI Manus Release”
[ ] Adicionar screenshots
[ ] Adicionar link para docs/UI_RELEASE_STRATEGY.md
[ ] Adicionar instruções de build
[ ] Adicionar instruções de integração com backend
[ ] Adicionar notas de segurança (X-Ketter-Client, CORS e API Base)

---

## 4. Homologação
[ ] Validar UI + Backend com 3 jobs reais:
    - Transfer move
    - Transfer copy
    - ZIP Smart folder transfer
[ ] Verificar:
    - KPIs
    - Donut
    - Throughput Chart
    - Alerts
    - Audit Logs
    - TransferDetails Panel
[ ] Confirmar que o design está consistente com Manus
[ ] Empacotar screenshots + dist/ + README para o release final

---

## 5. Commit Final
[ ] git add .
[ ] git commit -m "chore(ui): final release build + screenshots + README update"
[ ] pronto.


