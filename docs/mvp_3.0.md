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

## Estratégia de Transferência: DIRECT vs ZIP_FIRST (MVP 3.0)

### Motivação

Contexto real do Ketter nos studios:

- Pastas com **milhares de arquivos pequenos** (ex.: sessões de Pro Tools com 1.000–2.000 `.wav` de ~1 MB).
- Copiar arquivo a arquivo degradou brutalmente a performance (ex.: 2.000 arquivos → ~40 min).
- Ao empacotar em um único `.zip` sem compressão, a transferência de 1.6–2 GB foi praticamente instantânea.
- Para arquivos grandes ou poucas unidades, o overhead de zip não compensa.

Conclusão: precisamos de uma **estratégia automática** que escolha entre:

- `DIRECT` → copiar/mover arquivo a arquivo (engine atual).
- `ZIP_FIRST` → empacotar pasta em zip (sem compressão), transferir, descompactar no destino, limpar o lixo.

### Política v1 (MVP) – Critérios de Decisão

Política inicial (ajustável) para diretórios:

1. A estratégia `ZIP_FIRST` só é considerada se:

   - `source` for um diretório, **não** um arquivo único.
   - O número total de arquivos `N_files` dentro de `source` for maior que um limite.
   - O tamanho médio dos arquivos for "pequeno" (muitos arquivos pequenos é o problema real).

2. Caso contrário, usamos `DIRECT`.

Parâmetros default (v1):

- `N_FILES_ZIP_THRESHOLD`  
  - **Default**: `1000` arquivos  
  - Regra: se `N_files > 1000`, habilita candidata `ZIP_FIRST`.

- `AVG_FILE_SIZE_MAX_BYTES`  
  - **Default**: `4 * 1024 * 1024` (4 MiB)  
  - Regra: se `(total_bytes / N_files) < 4 MiB`, consideramos a pasta como “muitos arquivos pequenos”.

Política final v1:

- Se `source` **não** é diretório → `DIRECT`.
- Se `source` é diretório:
  - Calcula `N_files` e `total_bytes`.
  - Se `N_files > N_FILES_ZIP_THRESHOLD` **e** `avg_size = total_bytes / N_files < AVG_FILE_SIZE_MAX_BYTES`  
    → usar `ZIP_FIRST`.
  - Caso contrário → `DIRECT`.

Observação: esses limites são **heurísticos**, calibráveis via env vars em ambiente LAB:

- `KETTER_ZIP_THRESHOLD_FILES` (override de `N_FILES_ZIP_THRESHOLD`)
- `KETTER_ZIP_THRESHOLD_AVG_SIZE_BYTES` (override de `AVG_FILE_SIZE_MAX_BYTES`)

### Onde vive essa decisão na arquitetura

Para não transformar o código em um Frankenstein, a estratégia será isolada em uma **camada de planejamento**:

- Novo módulo: `mvp_core/transfer_engine/planner.py`

  Responsabilidades:

  - Definir um enum de estratégia:
    - `TransferStrategy = {DIRECT, ZIP_FIRST}`
  - Definir um plano de transferência:
    - `TransferPlan` com campos como:
      - `job: TransferJob`
      - `strategy: TransferStrategy`
      - talvez métricas pré-calculadas: `n_files`, `total_bytes`, `avg_size_bytes`
  - Função principal:
    - `decide_strategy(job: TransferJob) -> TransferPlan`
    - Implementa a política descrita acima:
      - Faz o walk em `job.source`, conta arquivos, soma bytes.
      - Lê thresholds das env vars (ou usa default).
      - Retorna um plano com `strategy = DIRECT` ou `ZIP_FIRST`.

- `mvp_core/worker/run.py` (scheduler simples do MVP):

  - Continua responsável por:
    - Buscar jobs `pending` no DB,
    - Atualizar status (`running` → `success/failed`),
    - Criar `JobEvent`.
  - Passos no loop:
    1. Carrega o `Job` do DB.
    2. Converte para `TransferJob` (como já acontece hoje).
    3. Chama `decide_strategy(transfer_job)` do `planner`.
    4. Se `strategy == DIRECT` → chama `run_transfer(...)` (engine atual).
    5. Se `strategy == ZIP_FIRST` → chama função específica (a ser implementada) que encapsula:
       - zip sem compressão,
       - transferência do zip,
       - unzip no destino,
       - limpeza de origem/destino temporários,
       - atualização de stats.

### O que **NÃO** entra no core `run_transfer` (por decisão explícita)

Para manter o core simples, estável e testável:

- A função `run_transfer(job: TransferJob)` **continua sendo apenas**:
  - “copie/mova este source para este destino”.
  - Sem conhecimento de zip, heurística, thresholds, estratégias.
- Toda a inteligência de “zip ou não zipar” fica:
  - no `planner` (decisão),
  - e em funções específicas do tipo `run_transfer_zip_first(plan)` (implementação ZIP_FIRST), **fora** do core atual.

Isso evita:

- Enfiar `if ZIP_FIRST` dentro de todo canto do engine.
- Misturar heurística de scheduler com lógica de I/O pura.
- Repetir a mesma decisão em UI, API, worker, etc.

### Roadmap de implementação para a Strategy

Passos futuros (próximas tarefas no MVP 3.0):

1. Criar `mvp_core/transfer_engine/planner.py` com:
   - `TransferStrategy` enum (`DIRECT`, `ZIP_FIRST`),
   - `TransferPlan` dataclass,
   - `decide_strategy(TransferJob)` implementando a política v1.

2. Atualizar `mvp_core/worker/run.py` para:
   - chamar `decide_strategy()` antes de executar a transferência,
   - logar qual estratégia foi usada no `JobEvent` (`"strategy=DIRECT"` ou `"strategy=ZIP_FIRST"`).

3. Implementar `run_transfer_zip_first(plan: TransferPlan)`:
   - criar zip sem compressão no source (ex.: `/tmp/ketter_tmp/...` ou ao lado do source),
   - transferir com `run_transfer` atual (apenas 1 arquivo),
   - descompactar no destino,
   - atualizar `Job.files_copied` e `Job.bytes_copied` com os dados pós-execução,
   - limpar temporários,
   - logar eventos detalhados (criação do zip, envio, extração, limpeza).

4. Refinar thresholds com base em testes reais:
   - Registar em `JobEvent`:
     - `n_files`,
     - `total_bytes`,
     - `avg_size_bytes`,
     - `strategy`.
   - Usar esses dados para ajustar `N_FILES_ZIP_THRESHOLD` e `AVG_FILE_SIZE_MAX_BYTES` em ambiente LAB antes de fixar defaults para produção.

---

Se você colar esse bloco no `docs/mvp_3.0.md`, a estratégia fica explicitamente documentada:

- Critérios objetivos,
- Onde a lógica vive,
- O que o core NÃO deve fazer,
- E um roadmap de implementação coerente.

Próximo passo, depois de registrar isso no doc, é a gente partir para o `planner.py` + ajuste do worker, mas agora com o contrato já escrito e não improvisado.

### Experimento inicial de ZIP_FIRST (lab)

- Dataset: 2000 arquivos ~1 KiB (total ~2 MB).
- DIRECT: 2000 arquivos copiados com sucesso, fanout intacto em `/data/dst_direct`.
- ZIP_FIRST (KETTER_ZIP_THRESHOLD_FILES=1): zip intermediário `~2.29 MB`, extração em `/data/dst_zip2/src`, mesma contagem de arquivos e bytes.
- Próximo passo: medir tempo de job (DIRECT vs ZIP_FIRST) em storage real de lab para calibrar thresholds.
