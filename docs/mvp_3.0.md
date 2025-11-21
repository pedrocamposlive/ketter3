# KETTER 3.0 — MVP CORE

## 1. Objetivo

Ter um núcleo do Ketter 3.0 capaz de:

- Cadastrar portais (origem/destino) e jobs de transferência.
- Executar transferências confiáveis entre dois hosts (ex.: LAB → SRVTRF).
- Usar a engine trio/zip para lidar bem com:
  - pasta pequena,
  - pasta com milhares de arquivos pequenos,
  - zip/deszip com limpeza.
- Registrar em Postgres:
  - jobs,
  - status,
  - eventos principais (start/end, erro).
- Ter um DKU mínimo que:
  - verifica DB, Redis, app, worker,
  - roda smoke test de transferência local,
  - gera relatório `.txt`/`.json` em `docs/dku_reports/`.

Isso precisa estar estável em 1 cenário real (LAB + 1 host remoto). Nada além disso é “MVP”.

---

## 2. Features que ENTRAM no MVP

1. **Modelo de dados mínimo em Postgres**
   - Tabelas:
     - `portals` (hosts / paths / credenciais).
     - `jobs` (tipo: copy/move, source, target, status, timestamps).
     - `job_events` (log simplificado por job).
   - Migrações Alembic funcionando em DEV (docker) e LAB.

2. **Engine de transferência consolidada**
   - Módulo isolado `mvp_core/transfer_engine/`.
   - Capaz de:
     - copiar pasta “normal” (poucos arquivos),
     - detectar pasta com muitos arquivos pequenos e optar por zip,
     - zipar sem compressão, mover, descompactar no destino,
     - limpar origem/destino conforme modo (copy vs move).
   - CLI interno para testes:
     - `python -m mvp_core.transfer_engine.cli --from A --to B --mode move`.

3. **API mínima (FastAPI)**
   - Em `mvp_core/app/`.
   - Endpoints:
     - `POST /jobs` – cria job.
     - `GET /jobs/{id}` – status.
     - `GET /jobs` – listagem simples.
   - Sem RBAC complexo por enquanto.

4. **Worker / fila assíncrona**
   - Em `mvp_core/worker/`.
   - Redis como broker.
   - Worker:
     - consome fila de jobs,
     - chama engine,
     - atualiza status no DB.

5. **DKU mínimo**
   - Em `mvp_core/dku/`.
   - Script único que:
     - verifica: Python, Postgres, Redis, app, worker;
     - roda smoke test: cria job local, executa, verifica DONE;
     - gera relatório `.txt` + `.json` em `docs/dku_reports/`.

6. **docker-compose PARA DEV/LAB**
   - Em `mvp_core/infra/`.
   - `docker-compose.yml` com:
     - `api`, `worker`, `postgres`, `redis`.
   - Scripts helpers:
     - `dev_up.sh`
     - `dev_down.sh`

---

## 3. Coisas PROIBIDAS até o MVP fechar

Enquanto o MVP 3.0 não estiver estável:

1. **UI nova (web), TUI, frontend bonitinho**
   - Nenhum esforço em UI fora de endpoints HTTP básicos.

2. **Refatoração estrutural grande do DKU legado**
   - O DKU antigo só é tocado se necessário para apontar para o MVP.
   - Sem “DKU 4.0” paralelo.

3. **Features avançadas de segurança / compliance**
   - RBAC avançado, multi-tenant completo, LDAP/SSO.
   - Por enquanto: credenciais mínimas, bem guardadas.

4. **Suporte first-class a Windows**
   - MVP é Linux/macOS. Windows entra depois.

5. **Integrações paralelas não ligadas a transferência**
   - Nada de media shuttle, clipping, n8n, etc., dentro do MVP.

---

## 4. Ordem de ataque

1. **Base DEV/LAB previsível**
   - `mvp_core/infra/docker-compose.yml` com:
     - `api`, `worker`, `postgres`, `redis`.
   - Scripts:
     - `dev_up.sh` / `dev_down.sh`.

2. **Engine de transferência isolada**
   - `mvp_core/transfer_engine/` com:
     - lógica de copy/move,
     - zip/unzip para pastas enormes,
     - interface clara (funções + CLI).

3. **DB + modelo mínimo**
   - Schema MVP,
   - Alembic configurado e rodando.

4. **API mínima + worker**
   - Criar job via API,
   - worker consome,
   - engine roda,
   - status em DONE/FAILED.

5. **DKU mínimo**
   - Script de check + smoke test + relatório.

6. **Teste real entre dois hosts**
   - LAB + 1 host remoto:
     - rodar MVP,
     - medir,
     - documentar.

---

## 5. Regra de ouro

Toda nova funcionalidade do Ketter 3.0 deve entrar em `mvp_core/`.  
Tudo que está fora disso é legado e só será mexido depois que o MVP estiver estável.
