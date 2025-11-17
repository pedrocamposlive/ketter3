# Smoke Test — Ketter UI + Backend Real
Versão 1.0

Este checklist garante que a interface React do Ketter está funcionando quando servida pelo backend FastAPI, com operações reais de watcher, transfers e auditoria.

---

## 1. Infraestrutura
### 1.1 Backend
- [ ] Rodar: `uvicorn app.main:app --reload`
- [ ] Verificar que inicia sem erros
- [ ] Checar logs de inicialização
- [ ] Checar conexão com DB real

### 1.2 Frontend
- [ ] Rodar build final (`npm run build`)
- [ ] Verificar presença do diretório `frontend/dist/`
- [ ] Confirmar assets: `.css`, `.js`, `.png`

### 1.3 Servindo UI pelo backend
- [ ] Abrir no navegador: `http://localhost:8000`
- [ ] Confirmar carregamento inicial sem erros no console

---

## 2. Dashboard
- [ ] Status geral carregando
- [ ] Latência/metrics aparecendo
- [ ] Alerts aparecendo
- [ ] Painéis sem erros no console

---

## 3. Transfers
- [ ] Abrir Transfers
- [ ] Simular um transfer real via watcher (colocar arquivo na pasta origem)
- [ ] Ver item surgindo na UI
- [ ] Conferir progresso em tempo real
- [ ] Checar checksum ao finalizar
- [ ] Conferir histórico

---

## 4. Audit
- [ ] Logs sendo exibidos pelo LogsViewer
- [ ] Atualização automática via polling
- [ ] Eventos exibidos: CREATE / MOVE / ZIP / UNZIP / FAIL

---

## 5. Settings
- [ ] Volumes carregados do backend real
- [ ] Estado de volumes correto
- [ ] Disponibilidade real aparecendo
- [ ] Alterações refletindo no backend (se permitido)

---

## 6. Security Wrappers
- [ ] Conferir headers enviados via Network tab
- [ ] Confirmar secureFetch() funcionando
- [ ] Confirmar wrapWithAudit() registrando eventos

---

## 7. Sistema de HealthCheck
- [ ] Abrir `/system-health`
- [ ] Conferir estado do watcher
- [ ] Conferir tempo de funcionamento
- [ ] Conferir conexão com banco

---

## 8. Conclusão
- [ ] Todos os itens acima passaram
- [ ] Atualizar `docs/state-ui.md`
- [ ] Criar commit: `chore: smoke test UI + backend validation`


