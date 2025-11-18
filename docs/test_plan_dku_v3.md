docs/test_plan_dku_v3.md

# DKU — Full Test Plan v3  
Deterministic Validation for macOS ARM

## 1. Pré-condições
- macOS limpo ou rollback executado.
- Nenhum serviço PostgreSQL/Redis rodando:


brew services stop postgresql@16
brew services stop redis

- Diretórios limpos:


rm -rf /opt/homebrew/var/postgresql@16
rm -rf /opt/homebrew/var/redis


---

## 2. Teste 00 — Hardware Check
**Objetivo:** validar arquitetura, RAM, disco e permissões.

**Comandos:**


./dku_run.sh


**Critérios:**
- Bloqueia execução se < 20GB livres.
- Apenas leitura, sem efeitos colaterais.

---

## 3. Teste 01 — System Prep
**Objetivo:** preparar ambiente, PATH, dependências básicas.

**Critérios:**
- PATH atualizado com Homebrew.
- Sem side effects persistentes.

---

## 4. Teste 02 — Dependencies (PostgreSQL + Redis)
**Objetivo:** instalação determinística de serviços.

**Critérios PostgreSQL:**
- Data directory recriado sempre.
- Serviço iniciado e respondendo a:


pg_isready -h 127.0.0.1


**Critérios Redis:**
- Data directory limpo.
- Serviço deve responder:


redis-cli ping


---

## 5. Teste 03 — Python Environment
**Objetivo:** venv determinístico com requirements corretos.

**Critérios:**
- venv recriado sempre.
- Pip, wheel, setuptools atualizados.
- Alembic importável.

---

## 6. Teste 03b — Redis Setup
**Objetivo:** reforço de garantia do Redis.

**Critérios:**
- Reseta redis data dir.
- Redis responde a:


redis-cli ping


---

## 7. Teste 04 — Post Install Validation (SAFE)
**Objetivo:** verificação leve e segura.

Checklist inclui:
- venv ativável
- PostgreSQL respondendo
- Redis respondendo
- Alembic importável
- app.main importável

---

## 8. Teste 05 — Report
**Objetivo:** gerar relatório final completo.

**Critérios:**
- Arquivo criado em docs/dku_reports
- Lista de logs, estados, serviços, dependências

---

## 9. Teste Final — Quick Manual E2E


./quickstart.sh
open http://127.0.0.1:8000/docs


**Critérios:**
- Backend sobe
- Endpoints respondem
- Serviços OK
- venv OK

---

## Resultado Esperado
Pipeline DKU executa:
- 00 → 01 → 02 → 03 → 03b → 04 → 05  
Sem falhas, sem resíduos, sem processos abertos.
