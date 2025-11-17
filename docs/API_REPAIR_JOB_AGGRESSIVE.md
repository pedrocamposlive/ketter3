# API_REPAIR_JOB_AGGRESSIVE.md
Ketter 3.0 — Full API Reconstruction Job
Modo Agressivo — Sincronização Completa UI ↔ Backend

Objetivo
--------
Reescrever completamente o arquivo frontend/src/services/api.js
com base no backend real FastAPI para eliminar:

- imports quebrados
- funções inexistentes
- endpoints faltantes
- funções antigas não usadas
- mismatches entre nome, path ou método
- erros de build do Vite gerados por APIs inconsistentes

Após a execução deste job, o frontend React estará 100% sincronizado
com o backend Ketter 3.0.

IMPORTANTE:
Este é o modo AGRESSIVO.
O Codex deve reconstruir tudo do zero e ignorar qualquer estado anterior.

--------------------------------------------------

Instruções para o Codex
-----------------------
Read STRATEGY_PROMPT.md.

Then read:
- app/main.py
- app/*.py
- app/routers/* (ou app/api/* dependendo da estrutura)
- docs/UI_RELEASE_STRATEGY.md
- docs/UI_RELEASE_BLUEPRINT.md
- docs/state-ui-manus.md

Then read:
- frontend/src/components/**/*.jsx
- frontend/src/pages/**/*.jsx
- frontend/src/layout/**/*.jsx

And finally:
- frontend/src/services/api.js  (somente para referência — será reescrito)

--------------------------------------------------

REQUIREMENTS
============

1. Reconstrução completa do api.js
----------------------------------
O Codex deve gerar um NOVO arquivo api.js contendo:

✔ wrapper seguro (secureFetch)
✔ todas as funções realmente existentes no backend
✔ nomes exatos, caminhos exatos, métodos exatos
✔ tratamento mínimo de erros
✔ exportações consistentes com o React

API obrigatória a reconstruir (baseada no backend Ketter 3.0):

Health:
  GET /health → getHealth()

Status:
  GET /status → getStatus()

Transfers:
  GET    /transfers?limit= → getTransfers()
  GET    /transfers/history/recent?days= → getRecentTransfers()
  POST   /transfers → createTransfer()
  DELETE /transfers/{id} → cancelTransfer()
  GET    /transfers/{id}/logs → getTransferLogs()
  GET    /transfers/{id}/checksums → getTransferChecksums()
  GET    /transfers/{id}/report → downloadTransferReport()

Audit Logs:
  GET /audit → getAuditLogs()

Alerts:
  GET /alerts → getAlerts()

Volumes:
  GET /volumes → getVolumes()
  GET /volumes/available → getAvailableVolumes()

Settings:
  GET /settings → getSettings()
  POST /settings → updateSettings()

--------------------------------------------------

2. Varredura e Reconciliação Completa do React
----------------------------------------------
O Codex deve:

✔ varrer todos os componentes React
✔ identificar todas as funções importadas de "../services/api"
✔ validar se estas funções existem no novo api.js
✔ criar as que faltam
✔ remover as que não existem no backend
✔ renomear se necessário
✔ atualizar imports automaticamente

Componentes que DEVEM ser revisados:

- FilePicker.jsx
- TransferCard.jsx
- TransferDetailsPanel.jsx
- TransferProgress.jsx
- TransferHistory.jsx
- AlertsPanel.jsx
- LogsViewer.jsx

Páginas que DEVEM ser revisadas:

- DashboardPage.jsx
- TransfersPage.jsx
- AuditPage.jsx
- SystemHealthPage.jsx
- SettingsPage.jsx

Layout que DEVE ser revisado:

- Layout.jsx

--------------------------------------------------

3. Limpeza Global
-----------------
O Codex deve:

✔ remover CSS morto em App.css relacionado a classes antigas  
✔ remover imports não utilizados  
✔ padronizar o uso de secureFetch e apiFetch  
✔ padronizar nomes de funções da API  
✔ garantir que nenhum componente importe algo inexistente  

--------------------------------------------------

4. Atualização de Documentação
-------------------------------
O Codex deve atualizar:

docs/state-ui-manus.md:

- Marcar “API Repair Aggressive” como concluído
- Criar entrada:
  PATCH API_REPAIR_AGGRESSIVE
  - lista de funções criadas
  - funções removidas
  - funções renomeadas
  - páginas e componentes atualizados
  - confirmação de que o React build deve passar agora

--------------------------------------------------

5. Commit Automático
---------------------
O Codex deve rodar:

git add .  
git commit -m "fix(ui/api): aggressive full API repair and React sync"

--------------------------------------------------

Regras de Execução
------------------
- Execute SOMENTE este job
- Pare após concluir o job
- Não fornecer comentários
- Não fornecer explicações
- Realizar apenas ações diretas

--------------------------------------------------

Objetivo Final
--------------
Após a execução com sucesso:

- Vite build deve passar sem erros
- Todos componentes React devem compilar
- api.js estará 100% sincronizado com backend
- importações estarão consistentes
- o frontend Ketter 3.0 estará finalizado

