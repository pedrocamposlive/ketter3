# Ketter — Organization State  
Versão 1.0  
Status de Reorganização Completa

---

- [x] Criar `ketter/app/core`
- [x] Criar `ketter/app/security`
- [x] Criar `ketter/app/services`
- [x] Criar `ketter/app/utils`
- [x] Criar `ketter/app/config`
- [x] Criar `ketter/tests/unit`
- [x] Criar `ketter/tests/integration`
- [x] Criar `ketter/tests/regression`
- [x] Criar `ketter/tests/hardening`
- [x] Criar `ketter/scripts`
- [x] Criar `docs/` (se não existir)

---

## 2. Movimentação do Código
- [x] Mover engine e watcher para `app/core`
- [x] Mover path sanitizer / whitelist para `app/security`
- [x] Mover worker_jobs, tasks e background features para `app/services`
- [x] Mover utilidades para `app/utils`
- [x] Mover configs e loaders para `app/config`
- [x] Corrigir imports após cada grupo movido

---

## 3. Testes
- [x] Rodar suite completa após reorganizar `core`
- [x] Rodar suite completa após reorganizar `security`
- [x] Rodar suite completa após reorganizar `services`
- [x] Rodar suite completa após reorganizar `utils`
- [x] Rodar suite completa após reorganizar `config`
- [x] Criar estrutura base para `tests/hardening`

---

## 4. Documentação
- [x] Mover strategy/blueprint/state para docs/
- [x] Atualizar README.md com nova estrutura
- [x] Criar architecture.png (placeholder)
- [x] Sincronizar todos os .md após conclusão

---

## 5. Scripts
- [x] Criar `scripts/ketter-dev.sh`
- [x] Criar `scripts/ketter-harden.sh`

---

## 6. Finalização
- [x] Validar import path global
- [x] Validar execução local e via Codex
- [x] Rodar suite final `pytest`
- [x] Marcar reorganização como concluída
