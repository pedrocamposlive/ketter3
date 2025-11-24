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

### Resultados de lab – 2000 arquivos pequenos (~1 KB cada)

Ambiente: macOS dev, SSD local, containers Docker (Postgres + Redis + API + Worker), bind mount `dev_data -> /data`.

| ID  | Modo | Estratégia   | Arquivos | Bytes    | Duração aprox. | Observações                         |
|-----|------|--------------|----------|----------|----------------|-------------------------------------|
| 9   | copy | DIRECT       | 2000     | 2,07 MB  | ~Xs            | `dev_data/src -> dev_data/dst_direct` |
| 11  | copy | ZIP_FIRST    | 2000     | 2,07 MB  | ~Ys            | `zip_size_bytes ≈ 2,29 MB`         |
| 12  | move | DIRECT       | 2000     | 2,07 MB  | ~Zs            | `src` removido, `dst_move_direct` ok |
| 15  | move | ZIP_FIRST    | 2000     | 2,07 MB  | ~Ws            | `src` removido, `dst_move_zip/src/*` |

Notas:

- Duração calculada como `updated_at - created_at`.
- Em storage real (Quantum/NFS/Samba), a diferença entre DIRECT e ZIP_FIRST tende a crescer bastante por causa de seek/latência, não por CPU.
- Este lab é só baseline funcional.

Preenche os `~Xs`, `~Ys`, etc. com os números que você extrair dos detalhes dos jobs.

Registrar só os três tempos coerentes:

job 9 (copy/direct) ≈ 1.63 s

job 11 (copy/zip) ≈ 1.76 s

job 15 (move/zip) ≈ 2.95 s

Sobre o job 12, eu colocaria explícito na doc:

“Job 12 (MOVE + DIRECT) apresentou duration_seconds ≈ 296s, mas isso inclui atraso de infraestrutura (worker antigo / restart), não representa tempo real de I/O. Será re-medido em lab dedicado.”

cat >> docs/mvp_3.0.md << 'EOF'

## Observability & Job Metrics (MVP Core)

### Endpoints de observabilidade

- `GET /jobs/{id}/detail`  
  - Retorna:
    - `status`, `mode`, `source_path`, `destination_path`
    - `files_copied`, `bytes_copied`
    - `duration_seconds` (derivado de `created_at`/`updated_at`)
    - `strategy` (derivada de eventos `strategy_decision`)
    - lista completa de `events` (created/started/strategy_decision/finished/error)

- `GET /stats/jobs-history`  
  - Query params:
    - `limit` (default: 20)
    - `mode` (ex.: `copy`, `move`)
    - `status` (ex.: `success`, `failed`)
    - `strategy` (ex.: `DIRECT`, `ZIP_FIRST`)
  - Retorna uma lista de jobs com:
    - `id`, `mode`, `status`
    - `strategy`, `duration_seconds`
    - `files_copied`, `bytes_copied`
    - `created_at`

#### Exemplos de uso

- Últimos 20 jobs de `move` com sucesso:

  ```bash
  curl "http://localhost:8000/stats/jobs-history?limit=20&mode=move&status=success" \
    | jq '.jobs[] | {id, mode, status, strategy, duration_seconds}'


## Lab Benchmark 02 — Storage de Rede / SAN (NAS, StorNext, Nexis)

Objetivo: medir o impacto real de DIRECT vs ZIP_FIRST em um ambiente mais próximo da pós-produção:

- Share de rede (SMB/NFS) ou volume de SAN (StorNext/Nexis),
- Latência maior,
- IOPS mais limitadas do que SSD local.

### Preparação do ambiente

1. **Montar o share/volume no host**

   Exemplos (ajustar para sua realidade):

   - macOS (SMB):

     ```bash
     mkdir -p /Volumes/KETTER_LAB
     mount_smbfs //usuario@servidor/share /Volumes/KETTER_LAB
     ```

   - Linux (CIFS):

     ```bash
     mkdir -p /mnt/ketter_lab
     mount -t cifs //servidor/share /mnt/ketter_lab \
       -o username=usuario,vers=3.1.1
     ```

2. **Mapear esse caminho para dentro dos containers**

   No `mvp_core/infra/docker-compose.yml`, o volume do serviço `api` e `worker` deve apontar para a raiz onde o dataset será criado, por exemplo:

   ```yaml
   services:
     api:
       volumes:
         - ../../dev_data:/data
         # ou, para testar direto no share:
         # - /Volumes/KETTER_LAB/dev_data:/data
     worker:
       volumes:
         - ../../dev_data:/data
         # ou:
         # - /Volumes/KETTER_LAB/dev_data:/data

         ## Lab 02 — Local SSD NEXIS/QUANTUM (ZIP_FIRST em disco real)

Objetivo: validar o motor de transferência (COPY/MOVE) usando discos reais montados no macOS, simulando NEXIS e QUANTUM, com estratégia `ZIP_FIRST` para cenários de muitas pequenas files.

### Infra utilizada

- Host: macOS (ambiente de desenvolvimento local).
- Volumes físicos:
  - `/Volumes/NEXIS`  → montado no container como `/mnt/nexis` (rw).
  - `/Volumes/QUANTUM` → montado no container como `/mnt/quantum` (rw).
- `docker-compose.yml` (serviços principais):
  - `postgres`:
    - `POSTGRES_USER=ketter_user`
    - `POSTGRES_PASSWORD=ketter_pass`
    - `POSTGRES_DB=ketter_mvp`
  - `redis`:
    - `redis:7`
  - `api`:
    - `DB_URL=postgresql+psycopg2://ketter_user:ketter_pass@postgres:5432/ketter_mvp`
    - `REDIS_URL=redis://redis:6379/0`
    - Volumes:
      - `../../dev_data:/data`
      - `/Volumes/NEXIS:/mnt/nexis:ro`
      - `/Volumes/QUANTUM:/mnt/quantum:rw`
  - `worker`:
    - `DB_URL` e `REDIS_URL` iguais ao `api`
    - Estratégia ZIP:
      - `KETTER_ZIP_THRESHOLD_FILES=100`
      - `KETTER_ZIP_THRESHOLD_AVG_SIZE_BYTES=4194304` (4 MiB)
    - Volumes:
      - `../../dev_data:/data`
      - `/Volumes/NEXIS:/mnt/nexis:ro`
      - `/Volumes/QUANTUM:/mnt/quantum:rw`

Banco acessado internamente por:
`postgresql+psycopg2://ketter_user:ketter_pass@postgres:5432/ketter_mvp`.

### Dataset do Lab

Para os testes, foram criados conjuntos de 2000 arquivos pequenos (~1 KiB de payload + overhead):

```bash
# Exemplo para MOVE:
python - << 'PYEOF'
from pathlib import Path

src = Path("/Volumes/NEXIS/ketter_lab/src_move_2000")
src.mkdir(parents=True, exist_ok=True)

N = 2000
for i in range(N):
    p = src / f"file_{i:04d}.txt"
    p.write_text(f"arquivo {i}\n" + "x" * 1024)
PYEOF

ls /Volumes/NEXIS/ketter_lab/src_move_2000 | wc -l  # 2000
du -sh /Volumes/NEXIS/ketter_lab/src_move_2000      # ~7.8M (on disk)


Se quiser, você pode ajustar os IDs dos jobs se depois rodar mais coisa e quiser “limpar” a narrativa, mas estruturalmente é isso.

---

## Lab 03 — próximo passo (proposta)

Antes de começar a rodar comando a esmo, vamos alinhar o alvo. No Lab 02 você provou:

- ZIP_FIRST funciona para 2000 arquivos pequenos em SSD local.
- COPY e MOVE estão corretos semântica e estruturalmente.
- Métrica básica (`duration_seconds`, `strategy`) está chegando redonda na API.

Agora você precisa sair do “happy path de 2000 arquivos pequenos” e começar a estudar:

1. Quando NÃO zipar (arquivos grandes).
2. Quando a vantagem do zip começa a aparecer de verdade.
3. Como isso se aproxima do cenário real (sessões com mix de arquivos).

Minha proposta para o Lab 03:

### Lab 03 — Arquivo grande e mix realista

1. **Caso 03.1 — Arquivo único grande (baseline sem ZIP)**  
   Objetivo: garantir que o engine fica em `DIRECT` para arquivos grandes, e medir o tempo.
   - Criar um arquivo grande (ex.: 5–10 GiB) em `/Volumes/NEXIS/ketter_lab/src_big_01`.
   - Rodar job:
     - `mode="copy"`
     - `source_path=/mnt/nexis/ketter_lab/src_big_01`
     - `destination_path=/mnt/quantum/ketter_lab/dst_big_01`
   - Esperado:
     - `strategy = DIRECT`
     - `files_copied = 1`
     - `duration_seconds` registrado.
   - Se o engine tentar usar ZIP_FIRST aqui, temos bug de heurística.

2. **Caso 03.2 — Mix: 1 arquivo grande + 2000 pequenos**  
   Objetivo: ver como a estratégia se comporta num cenário mais próximo de sessão real (grandes + pequenos).
   - Montar algo como:
     - `/Volumes/NEXIS/ketter_lab/src_mix_01/SESSION.ptx` (ou só um `.bin` grande).
     - `/Volumes/NEXIS/ketter_lab/src_mix_01/audio/file_0000.wav ... file_1999.wav` (pequenos).
   - Rodar job:
     - `mode="copy"` (depois `move`).
   - Ver:
     - `n_files`, `avg_size`, `strategy`, `duration_seconds`.
   - Aqui vai aparecer se a heurística “puxa para ZIP_FIRST cedo demais” ou não.

3. **Caso 03.3 — Sweep de thresholds (afinando heurística)**  
   Ainda em SSD, mas agora mexendo em:

   - `KETTER_ZIP_THRESHOLD_FILES`
   - `KETTER_ZIP_THRESHOLD_AVG_SIZE_BYTES`

   Ideia:

   - Rodar a mesma carga (ex.: `src_2000` e `src_mix_01`) com:
     - `FILES = 50, 100, 500`
     - `AVG_SIZE_BYTES = 1 MiB, 4 MiB, 16 MiB`
   - Anotar:
     - `strategy` escolhido.
     - `duration_seconds`.
   - Isso te dá um início de tabela para decidir defaults “sensatos” para ambiente real.

Se você concordar com essa linha, no próximo passo eu já te mando:

- Bloco em shell com os comandos para criar o arquivo grande e o mix (03.1 e 03.2).
- O payload certinho dos `curl` para os jobs.
- Um mini-template em markdown para você já deixar o “Lab 03” pronto no `mvp_3.0.md` enquanto coleta os números.

E aqui vou ser chato de propósito: se você não medir DIRECT vs ZIP_FIRST no mesmo par de volumes para o mesmo payload, você vai acabar escolhendo threshold na intuição, não em dado. Esse é o ponto cego clássico de motor de transferência. Vamos evitar isso já no Lab 03.

### Lab 03 — Testes em discos reais (NEXIS / QUANTUM)

Ambiente:

- NEXIS e QUANTUM montados no macOS:
  - `/Volumes/NEXIS`
  - `/Volumes/QUANTUM`
- Docker mapeando os volumes:
  - `/mnt/nexis` → `/Volumes/NEXIS`
  - `/mnt/quantum` → `/Volumes/QUANTUM`
- DB/Redis rodando dentro do docker-compose (`postgres`, `redis`, `api`, `worker`).

#### 03.1 — COPY de 1 arquivo grande (5 GiB)

Setup:

- Origem: `/Volumes/NEXIS/ketter_lab/src_big_01/big_05GiB.bin`
- Destino: `/Volumes/QUANTUM/ketter_lab/dst_big_01`

Job:

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/mnt/nexis/ketter_lab/src_big_01",
    "destination_path": "/mnt/quantum/ketter_lab/dst_big_01",
    "mode": "copy"
  }'
# → id = 2
Resultado (jobs/2/detail):

strategy = DIRECT

files_copied = 1

bytes_copied = 5.368.709.120 (~5 GiB)

duration_seconds ≈ 28.08

status = success

Checks no filesystem:

ls /Volumes/QUANTUM/ketter_lab/dst_big_01 → big_05GiB.bin.

Tamanhos em bytes de origem/destino (ls -l) idênticos.

Conclusão: motor escolheu corretamente DIRECT para arquivo único grande e completou o copy com consistência de tamanho.

03.2 — MIX (2 GiB + 2000 arquivos pequenos), modos COPY e MOVE

Setup:

Origem: /Volumes/NEXIS/ketter_lab/src_mix_01

session_2GiB.bin (~2 GiB)

audio/clip_XXXX.wav (2000 arquivos pequenos).

Contagem:

find src_mix_01 -type f | wc -l → 2001.

du -sh src_mix_01 → ~2.0G.

03.2.a — COPY

Job:

curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/mnt/nexis/ketter_lab/src_mix_01",
    "destination_path": "/mnt/quantum/ketter_lab/dst_mix_copy_01",
    "mode": "copy"
  }'
# → id = 3


Resultado (jobs/3/detail):

strategy = ZIP_FIRST

files_copied = 2001

bytes_copied ≈ 2.149.552.538

duration_seconds ≈ 27.29

status = success

Checks no filesystem:

find /Volumes/QUANTUM/ketter_lab/dst_mix_copy_01 -type f | wc -l → 2001.

Hierarquia preservada: dst_mix_copy_01/src_mix_01/session_2GiB.bin + src_mix_01/audio/clip_XXXX.wav.

du -sh dst_mix_copy_01 → ~2.0G.

Observação operacional: leituras de FS feitas antes do status = success podem mostrar contagens parciais (falso negativo). O fluxo correto é: checar status, depois validar o FS.

03.2.b — MOVE

Job:

curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/mnt/nexis/ketter_lab/src_mix_01",
    "destination_path": "/mnt/quantum/ketter_lab/dst_mix_move_01",
    "mode": "move"
  }'
# → id = 4


Resultado (jobs/4/detail):

strategy = ZIP_FIRST

duration_seconds ≈ 1.67

status = success (job finalizado com sucesso).

Checks:

Origem:

ls /Volumes/NEXIS/ketter_lab/src_mix_01 → No such file or directory (comportamento esperado para MOVE).

Destino:

find /Volumes/QUANTUM/ketter_lab/dst_mix_move_01 -type f | wc -l → 2001.

du -sh /Volumes/QUANTUM/ketter_lab/dst_mix_move_01 → ~2.0G.

Estrutura preservada: dst_mix_move_01/src_mix_01/....

Conclusão geral Lab 03:

Engine está se comportando como esperado em ambiente “real” NEXIS/QUANTUM:

Arquivo único grande → DIRECT.

MIX (muitos pequenos + 1 grande) → ZIP_FIRST.

Semântica de COPY e MOVE preservadas.

Métricas de tempo, contagem e bytes alinhadas com o esperado, inclusive em volumes reais de teste.

cat >> docs/mvp_3.0.md << 'EOF'

## Lab04 — Estratégia ZIP_FIRST vs DIRECT em SSD local (NEXIS x QUANTUM)

### Objetivo

Validar o comportamento da heurística de estratégia (`ZIP_FIRST` vs `DIRECT`) e medir tempos reais de cópia/move em um cenário mais próximo do ambiente Nexis/Quantum, usando dois SSDs locais:

- `/Volumes/NEXIS`  → montado como `/mnt/nexis` no container
- `/Volumes/QUANTUM` → montado como `/mnt/quantum` no container

O foco do Lab04 foi:

1. Confirmar se a escolha de estratégia está coerente com o perfil dos dados:
   - Muitos arquivos pequenos → `ZIP_FIRST`
   - Poucos arquivos grandes → `DIRECT`
2. Validar tempos de transferência em cenários representativos.
3. Verificar coerência das estatísticas expostas pela API:
   - `/jobs/{id}/detail`
   - `/stats/jobs-history`

---

### Cenários testados

#### 1. MOVE de 2000 arquivos pequenos (NEXIS → QUANTUM, ZIP_FIRST)

- Setup:

  - Origem:
    - `/Volumes/NEXIS/ketter_lab/src_move_2000` (2000 arquivos `.txt` ~1 KiB)
  - Destino:
    - `/Volumes/QUANTUM/ketter_lab/dst_move_2000`
  - Job:
    - `mode: "move"`
    - `source_path: "/mnt/nexis/ketter_lab/src_move_2000"`
    - `destination_path: "/mnt/quantum/ketter_lab/dst_move_2000"`

- Observações principais:

  - Job:
    - `id: 1`
    - `strategy: "ZIP_FIRST"`
    - `status: "success"`
    - `files_copied: 2000`
    - `bytes_copied: 2072890`
    - `duration_seconds ≈ 3.38`
  - Layout de destino:
    - Origem:
      - `/Volumes/NEXIS/ketter_lab/src_move_2000/file_XXXX.txt`
    - Destino:
      - `/Volumes/QUANTUM/ketter_lab/dst_move_2000/src_move_2000/file_XXXX.txt`
  - Origem removida corretamente (como esperado para `mode = move`).

#### 2. COPY de 2000 arquivos pequenos (NEXIS → QUANTUM, ZIP_FIRST)

- Setup:

  - Origem:
    - `/Volumes/NEXIS/ketter_lab/src_2000`
  - Destino:
    - `/Volumes/QUANTUM/ketter_lab/dst_2000`
  - Job:
    - `mode: "copy"`
    - `source_path: "/mnt/nexis/ketter_lab/src_2000"`
    - `destination_path: "/mnt/quantum/ketter_lab/dst_2000"`

- Observações principais:

  - Job:
    - `id: 3`
    - `strategy: "ZIP_FIRST"`
    - `status: "success"`
    - `files_copied: 2000`
    - `bytes_copied: 2072890`
    - `duration_seconds ≈ 3.03`
  - Layout de destino:
    - Destino final:
      - `/Volumes/QUANTUM/ketter_lab/dst_2000/src/file_XXXX.txt`
  - Origem preservada (como esperado para `mode = copy`).

#### 3. COPY de 1 arquivo grande (5 GiB) — NEXIS → QUANTUM (DIRECT)

- Setup:

  - Origem:
    - `/Volumes/NEXIS/ketter_lab/src_big_01/big_05GiB.bin` (~5 GiB no teste inicial, e outro cenário com 1 GiB em `dev_data`)
  - Destino:
    - `/Volumes/QUANTUM/ketter_lab/dst_big_01`
  - Job:
    - `mode: "copy"`
    - `source_path: "/mnt/nexis/ketter_lab/src_big_01"`
    - `destination_path: "/mnt/quantum/ketter_lab/dst_big_01"`

- Observações principais (job real em `dev_data` com 1 GiB):

  - Job:
    - `id: 7`
    - `strategy: "DIRECT"`
    - `status: "success"`
    - `files_copied: 1`
    - `bytes_copied: 1073741824`
    - `duration_seconds ≈ 4.63`
  - Layout de destino (caso `dev_data`):
    - Origem:
      - `dev_data/src_big_01/big_01GiB.bin`
    - Destino:
      - `dev_data/dst_big_01/big_01GiB.bin`
    - Ou seja: sem subpasta `src_big_01` no destino.

---

### 4. Cenário misto (sessão grande + muitos arquivos pequenos)

- Setup:

  - Origem:
    - Base: `/Volumes/NEXIS/ketter_lab/src_mix_01`
    - Arquivo grande:
      - `/Volumes/NEXIS/ketter_lab/src_mix_01/session_2GiB.bin`
    - Áudio pequeno:
      - `/Volumes/NEXIS/ketter_lab/src_mix_01/audio/clip_XXXX.wav` (2000 arquivos pequenos)
  - Copy:
    - `destination_path: "/mnt/quantum/ketter_lab/dst_mix_copy_01"`
    - Job `id: 3` (Lab mix)
    - `mode: "copy"`
  - Move:
    - `destination_path: "/mnt/quantum/ketter_lab/dst_mix_move_01"`
    - Job `id: 4`
    - `mode: "move"`

- Observações principais:

  - COPY (`id: 3`):
    - `strategy: "ZIP_FIRST"`
    - `status: "success"`
    - `files_copied: 2001`
    - `bytes_copied ≈ 2.0 GiB`
    - `duration_seconds ≈ 27.29`
    - Layout destino:
      - `/Volumes/QUANTUM/ketter_lab/dst_mix_copy_01/src_mix_01/session_2GiB.bin`
      - `/Volumes/QUANTUM/ketter_lab/dst_mix_copy_01/src_mix_01/audio/clip_XXXX.wav`
  - MOVE (`id: 4`):
    - `strategy: "ZIP_FIRST"`
    - `status: "success"`
    - `files_copied: 2001`
    - `bytes_copied ≈ 2.0 GiB`
    - `duration_seconds ≈ 28.19`
    - Origem removida:
      - `/Volumes/NEXIS/ketter_lab/src_mix_01` não existe após o job.
    - Layout destino:
      - `/Volumes/QUANTUM/ketter_lab/dst_mix_move_01/src_mix_01/...` (estrutura preservada)

---

### 5. Stats e filtros da API

Foram validados os endpoints:

- `GET /stats/jobs-history?limit=10`
- Filtros:
  - `mode=copy&status=success`
  - `strategy=ZIP_FIRST`
  - `strategy=DIRECT`
  - `limit=5` com projeção parcial via `jq`

Exemplo de último snapshot relevante:

- Jobs com sucesso (resumido):

  - Pequenos (ZIP_FIRST):
    - `id=5` → `src_small_01` → `duration ≈ 1.30s`, `files_copied=2000`
    - `id=6` → `src_small_02` → `duration ≈ 2.35s`, `files_copied=2000`
  - Mistos (ZIP_FIRST):
    - `id=3` e `id=4` → `src_mix_01` → `duration ≈ 27–28s`, `files_copied=2001`
  - Grandes (DIRECT):
    - `id=7` → `src_big_01` → `duration ≈ 4.63s`, `files_copied=1`, `bytes_copied=1 GiB`

Conclusão:

- A heurística de seleção de estratégia está funcionando como esperado:
  - Muitos arquivos pequenos → `ZIP_FIRST` é consistente e bem mais eficiente.
  - Poucos arquivos grandes → `DIRECT` é escolhido e entrega tempo coerente.
- O endpoint `/stats/jobs-history` já fornece uma visão útil de:
  - Tempo por job
  - Estratégia adotada
  - Volume de arquivos e bytes
  - Filtros por `mode`, `status`, `strategy`

---

### Observação importante (contrato de layout)

Durante o Lab04 foi identificado um comportamento inconsistente do layout de destino entre as estratégias:

- Estratégia `ZIP_FIRST`:
  - Para diretórios, o destino inclui o `basename(source_path)` como subpasta:
    - Exemplo:
      - Source: `/mnt/nexis/ketter_lab/src_mix_01`
      - Destino: `/mnt/quantum/ketter_lab/dst_mix_copy_01/src_mix_01/...`
- Estratégia `DIRECT`:
  - Para diretórios, o destino **não** inclui o `basename(source_path)`:
    - Exemplo:
      - Source (dev_data): `dev_data/src_big_01/big_01GiB.bin`
      - Destino: `dev_data/dst_big_01/big_01GiB.bin`
      - Esperado para consistência de contrato: `dev_data/dst_big_01/src_big_01/big_01GiB.bin`

Isso significa que, hoje:

- O layout de destino não é invariável em relação à estratégia de transferência.
- O operador/consumidor do Ketter precisa conhecer detalhes internos da estratégia (`ZIP_FIRST` vs `DIRECT`) para saber onde exatamente o conteúdo vai aparecer, o que é indesejável.

---

### TODO — Unificar layout entre DIRECT e ZIP_FIRST

Para evitar surpresas em produção (Nexis/Quantum) e manter o contrato de API limpo, foi registrado o seguinte TODO de arquitetura:

> Unificar layout de destino entre DIRECT e ZIP_FIRST: sempre `dest/<basename(source)>/...` para diretórios.

Regras propostas:

1. Se `source_path` for um **diretório**:
   - Layout canônico:
     - `destination_root = destination_path / basename(source_path)`
   - Todas as estratégias (`DIRECT`, `ZIP_FIRST`, futuras) devem escrever a árvore a partir de `destination_root`.
   - Exemplos esperados:
     - `/mnt/nexis/ketter_lab/src_small_01` → `/mnt/quantum/ketter_lab/dst_small_01/src_small_01/...`
     - `/mnt/nexis/ketter_lab/src_big_01` → `/mnt/quantum/ketter_lab/dst_big_01/src_big_01/big_XX.bin`
     - `/mnt/nexis/ketter_lab/src_mix_01` → `/mnt/quantum/ketter_lab/dst_mix_copy_01/src_mix_01/...`
2. Se `source_path` for um **arquivo único**:
   - Layout canônico:
     - `destination_root = destination_path`
     - Arquivo em:
       - `destination_path / basename(source_path)`
   - Exemplo:
     - `/mnt/nexis/INGEST/clip_0001.mov` → `/mnt/quantum/INGEST_STG/clip_0001.mov`

Impacto:

- O comportamento atual do ZIP_FIRST já está próximo do contrato desejado (usa o `basename` da pasta).
- A principal mudança será alinhar o caminho DIRECT para respeitar o mesmo padrão para diretórios, garantindo que a escolha da estratégia não afete o layout final.

EOF

cat >> docs/mvp_3.0.md << 'EOF'

## Lab05 — Casos de erro (paths inválidos, permissão, espaço em disco)

### Objetivo

Validar o comportamento do engine e da API em cenários de erro, garantindo que:

1. Jobs com problemas previsíveis **não** fiquem pendurados em `running` indefinidamente.
2. `status` seja marcado corretamente como `"failed"`.
3. Eventos (`job_events`) registrem mensagens úteis (ex.: `source_not_found`, `permission_denied`, etc.).
4. Não haja efeitos colaterais perigosos:
   - Nenhum arquivo parcialmente copiado/movido em paths inesperados.
   - Origem não alterada em cenários de erro de `copy`.
5. A API de stats (`/stats/jobs-history`) reflita esses jobs com falha, permitindo análise posterior.

### Escopo deste Lab

Nesta iteração, o foco é:

1. **Fonte inexistente**  
   - `source_path` aponta para um diretório que não existe.
   - Esperado: falha rápida, sem criar estrutura de destino.

2. **Destino sem permissão para escrita (read-only)**  
   - Job tentando escrever em um mount configurado como somente leitura.
   - Esperado: falha com erro de permissão, sem arquivos parcialmente escritos.

3. **Erros genéricos de I/O (pré-validação)**  
   - Garantir que qualquer exceção de I/O antes/ durante a transferência resulte em:
     - `status = "failed"`
     - mensagem de erro registrada em `events`
     - nenhuma alteração inesperada na origem.

**Obs.:** O teste de “disco cheio” real será tratado em um Lab dedicado (provável Lab06), com volume limitado/simulado. Aqui, o foco é validar o *tratamento* de erro, não esgotar fisicamente o disco da máquina do operador.

### TODO Lab05

- [ ] Executar cenários:
  - [ ] L05-01: `source_path` inexistente (copy).
  - [ ] L05-02: `destination_path` em volume read-only.
  - [ ] L05-03: validar resposta da API (`jobs/{id}/detail`, `stats/jobs-history`) para jobs com falha.
- [ ] Registrar, para cada cenário:
  - `id`, `mode`, `strategy`, `status`
  - mensagens em `events`
  - layout real observado em disco (se houver).
- [ ] A partir dos resultados, decidir:
  - Naming padronizado para tipos de erro (ex.: `source_not_found`, `dest_permission_denied`, `io_error`).
  - Ajustes de mapeamento de exceções → eventos.

  ### Lab05 — Cenários de falha (MVP infra)

**L05-01 — Source inexistente**

- Job: `/data/source_does_not_exist_01 → /data/dst_error_source_missing_01` (mode=copy).
- Resultado:
  - Destino `dev_data/dst_error_source_missing_01` **não foi criado**.
  - Job marcado como `failed` (ver `/jobs/10/detail`).
  - Nenhum arquivo copiado.
- Conclusão:
  - Fluxo mínimo de erro para “source inexistente” está funcionando: não suja o destino.

**L05-02 — Tentativa de “destino read-only” (QUANTUM → NEXIS)**

- Job: `/mnt/quantum/ketter_lab/src_perm_ro_01 → /mnt/nexis/ketter_lab/dst_perm_ro_01` (mode=copy).
- Expectativa: erro de permissão ao escrever no NEXIS.
- Achados:
  - Dentro do container, ambos mounts aparecem como `rw`:

    - `/run/host_mark/Volumes on /mnt/quantum type fakeowner (rw,...)`
    - `/run/host_mark/Volumes on /mnt/nexis type fakeowner (rw,...)`

  - Job `11` foi concluído com sucesso:

    - `status = "success"`
    - `files_copied = 20`
    - `bytes_copied = 20790`
    - Evento `finished` sem erro.
  - Destino `/Volumes/NEXIS/ketter_lab/dst_perm_ro_01` contém os 20 arquivos esperados (~80K).

- Conclusão:
  - Este teste **não validou permissão negada**.  
  - O bind-mount `:ro` para `/Volumes/NEXIS` não é respeitado pelo driver `fakeowner` do Docker Desktop/macOS neste setup.
  - Cenários de `PermissionError` ainda não foram exercitados de forma confiável; precisamos de:
    - OU um ambiente Linux “real” com mount `ro`/ACLs,
    - OU um cenário de teste sintético que force erro de escrita dentro do container (ex.: diretório com `chmod 555` / path protegido).

**TODO (Lab05)**

- [ ] Criar cenário reprodutível de `PermissionError` dentro do container (sem depender de `/Volumes` + `fakeowner`).
- [ ] Garantir que jobs com `PermissionError` sejam marcados como `failed` com:
  - `files_copied`/`bytes_copied` coerentes,
  - evento `error` com mensagem descritiva.

  ### Lab05 — Cenários de falha (MVP infra, revisão)

**L05-01 — Source inexistente**

- Job: `/data/source_does_not_exist_01 → /data/dst_error_source_missing_01` (mode=copy).
- Resultado observado:
  - Destino `dev_data/dst_error_source_missing_01` **não foi criado**.
  - `GET /jobs/10/detail` mostra o job como `failed` (sem arquivos copiados).
- Conclusão:
  - Fluxo mínimo de erro para “source inexistente” está funcionando: o engine não cria destino nem deixa lixo parcial.

**L05-02 — Tentativa de “destino read-only” (QUANTUM → NEXIS)**

- Job: `/mnt/quantum/ketter_lab/src_perm_ro_01 → /mnt/nexis/ketter_lab/dst_perm_ro_01` (mode=copy).
- Expectativa teórica: erro de permissão ao escrever em NEXIS.
- Achados práticos:
  - Dentro do container, os mounts aparecem como:

        /run/host_mark/Volumes on /mnt/quantum type fakeowner (rw,...)
        /run/host_mark/Volumes on /mnt/nexis   type fakeowner (rw,...)

  - `GET /jobs/11/detail`:

    - `status = "success"`
    - `files_copied = 20`
    - `bytes_copied ≈ 20 KB`
    - evento `finished` sem erro.

  - No host, `/Volumes/NEXIS/ketter_lab/dst_perm_ro_01` contém os 20 arquivos.
- Conclusão:
  - Este teste **não validou cenário de permissão negada**.
  - O bind-mount `:ro` em `/Volumes/...` está sendo neutralizado pelo driver `fakeowner` do Docker Desktop/macOS neste setup.
  - Cenários de `PermissionError` reais ainda não foram exercitados; precisam de:
    - ambiente Linux real com mount `ro`/ACLs reais **ou**
    - cenários sintéticos dentro do container que forcem `PermissionError` sem depender de `/Volumes`.

    ### Lab06 — Unificação de layout (DIRECT vs ZIP_FIRST)

Objetivo: garantir que, para qualquer diretório de origem, o layout de destino seja
sempre:

- `destination_root/<basename(source)>/...`

Tanto para estratégia `DIRECT` quanto para `ZIP_FIRST`.

**Cenário 1 — Diretório grande (1 arquivo de 1 GiB, DIRECT)**

- Source: `dev_data/src_big_01/big_01GiB.bin`
- Job:
  - `source_path = "/data/src_big_01"`
  - `destination_path = "/data/dst_big_01_layout"`
  - `mode = "copy"`
- Resultado (`/jobs/12/detail`):
  - `strategy = "DIRECT"`
  - `status = "success"`
  - `files_copied = 1`
  - `bytes_copied = 1073741824`
- Layout no filesystem host:
  - `dev_data/dst_big_01_layout/src_big_01/big_01GiB.bin`
  - `du -sh dev_data/src_big_01 dev_data/dst_big_01_layout` → ambos ≈ `1.0G`

**Cenário 2 — Diretório com muitos arquivos pequenos (ZIP_FIRST)**

- Source: `dev_data/src_small_01/file_0000.txt ... file_1999.txt`
- Job:
  - `source_path = "/data/src_small_01"`
  - `destination_path = "/data/dst_small_zip_01"`
  - `mode = "copy"`
- Resultado:
  - `strategy = "ZIP_FIRST"`
  - `status = "success"`
- Layout no filesystem host:
  - `dev_data/dst_small_zip_01/src_small_01/file_XXXX.txt` (2000 arquivos)

**Conclusão**

- O layout de destino está unificado entre `DIRECT` e `ZIP_FIRST` para diretórios:
  - sempre `destination_root/<basename(source)>/...`.
- Isso evita surpresas no Ketter UI / relatórios, que agora podem assumir um esquema
  consistente tanto para jobs zipados quanto diretos.

### Semântica de overwrite (MVP — modo seguro)

Regra oficial para o MVP 3.0:

- Para jobs cujo `source` é um diretório:
  - O destino lógico é sempre `destination_root/<basename(source)>`.
  - **Se este diretório de destino já existir**, o job **FALHA imediatamente**,
    sem tocar em nenhum arquivo, com erro do tipo:
    - `Destination already exists: <dest_root>/<basename(source)>`

Motivação:

- Evitar sobrescrita acidental de diárias (“envia de novo” sem pensar).
- Forçar que qualquer comportamento de overwrite seja **explícito** no futuro
  (flag, modo avançado, política específica de reprocessamento).
- Manter a engine previsível para reprocessamento, retries e integração com
  fluxos Pro Tools / diárias.

  ## Lab07 — Overwrite & idempotência (planejado)

Objetivo: exercitar e validar a semântica de overwrite em modo seguro, cobrindo:

- Execução repetida do mesmo job (mesmo source/dest).
- Comportamento de `jobs-history` em runs repetidos.
- Comportamento quando o destino já existe antes mesmo do primeiro job.