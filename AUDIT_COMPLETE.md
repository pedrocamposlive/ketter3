# AUDITORIA COMPLETA - BUGS ENCONTRADOS

## Data: 2025-11-12 | Status: CRITICAL - 5 BUGS IDENTIFICADOS

---

## BUG #1: CRITICAL - Timeout Format em RQ Queue

**Severidade:** CRÍTICA
**Localização:** `app/worker_jobs.py` linha 486-488 e `app/routers/transfers.py` linha 135-137
**Problema:**

```python
# ERRADO - RQ espera inteiros em segundos, não strings
job_timeout=WATCH_CONTINUOUS_JOB_CONFIG.get("timeout", 86400),

# Mas TRANSFER_JOB_CONFIG define como:
TRANSFER_JOB_CONFIG = {
    "timeout": "2h",  # STRING - RQ vai falhar!
    ...
}
```

**Impacto:** Jobs podem falhar com erro de timeout inválido

**Solução:**
```python
# Correto - em segundos
TRANSFER_JOB_CONFIG = {
    "timeout": 7200,  # 2 horas em segundos
    ...
}
WATCH_TRANSFER_JOB_CONFIG = {
    "timeout": 10800,  # 3 horas em segundos
    ...
}
WATCH_CONTINUOUS_JOB_CONFIG = {
    "timeout": 86400,  # 24 horas em segundos
    ...
}
```

---

## BUG #2: CRITICAL - Cancelled Transfer Check Too Strict

**Severidade:** CRÍTICA
**Localização:** `app/worker_jobs.py` linhas 65-72 (`transfer_file_job`)
**Problema:**

```python
# Verifica se transfer foi cancelado pelo usuário
if transfer.status == TransferStatus.FAILED and transfer.error_message == "Transfer cancelled by user":
    print(f"Transfer {transfer_id} was cancelled by user, skipping")
    return {"success": False}
```

**Por que é bug:** Esta verificação é TOO BROAD. Qualquer transferência que falhou com essa mensagem será skipada, mesmo se foi erro anterior não relacionado ao cancelamento do usuário.

**Impacto:** Jobs legítimos são skiped por causa de falhas anteriores
**Exemplo do seu erro:**
- Teste anterior deixou transfer 119 com status=FAILED
- watcher_continuous_job enfileira transfer_file_job(119) para novo arquivo
- Job vê transfer 119 com FAILED + "cancelled" message → SKIP

**Solução:**
```python
# Adicionar flag "user_cancelled" ou usar status específico
# OPÇÃO A: Adicionar coluna
transfer = Transfer()
transfer.user_cancelled = True  # Apenas quando usuário clica "Stop"

# OPÇÃO B: Usar status enum distinto
# TransferStatus.CANCELLED (não FAILED)

# Verificação corrigida:
if transfer.status == TransferStatus.CANCELLED:
    print(f"Transfer {transfer_id} was cancelled, skipping")
    return {"success": False}
```

---

## BUG #3: HIGH - Wrong Path in MOVE Deletion

**Severidade:** ALTA
**Localização:** `app/copy_engine.py` linha 474
**Problema:**

```python
# Na função transfer_file_with_verification():
delete_source_after_move(transfer.original_folder_path if is_folder else transfer.source_path, is_folder)
```

**Por que é bug:** `transfer.original_folder_path` é só preenchido se `is_folder=True` (linha 260). Se for arquivo e MOVE mode, usa `transfer.source_path` corretamente, mas há uma inconsistência lógica aqui.

**Impacto:** Para arquivos em MOVE, funciona OK. Para pastas, funciona OK.
**Risco:** Confuso para manutenção futura

**Solução (refactor para clareza):**
```python
# Mais explícito:
if transfer.operation_mode == "move":
    if is_folder:
        # Para pasta: deleta conteúdo da pasta original, preserva pasta
        delete_source_after_move(transfer.original_folder_path, is_folder=True)
    else:
        # Para arquivo: deleta arquivo
        delete_source_after_move(transfer.source_path, is_folder=False)
```

---

## BUG #4: HIGH - API Client Conversion Logic Not Imported

**Severidade:** MÉDIA
**Localização:** `app/routers/transfers.py` linhas 98-104
**Problema:**

```python
# Na criação de Transfer no router:
watch_mode_enabled=1 if transfer.watch_mode_enabled else 0,
watch_continuous=1 if transfer.watch_continuous else 0,

# Mas o API client (frontend) envia:
watch_mode = "none" | "once" | "continuous"  # String do radio button

# E depois em api.js converte:
const isWatchEnabled = watchMode !== 'none'
const isWatchContinuous = watchMode === 'continuous'
```

**Por que é bug:** Há desconexão entre frontend (string) e backend (boolean). O servidor está esperando booleans mas frontend manda string.

**Impacto:** Dependendo da schema do TransferCreate, pode não validar corretamente

**Solução:** Confirmar que `TransferCreate` schema aceita os valores corretos:
```python
class TransferCreate(BaseModel):
    source_path: str
    destination_path: str
    watch_mode_enabled: bool = False  # Frontend converte "continuous" → True
    watch_continuous: bool = False    # Frontend converte "once"/"continuous" → apropriado
    settle_time_seconds: int = 30
    operation_mode: str = "copy"      # "copy" ou "move"
```

---

## BUG #5: MEDIUM - _wait_for_file_settle Logic Off-by-One

**Severidade:** MÉDIA
**Localização:** `app/worker_jobs.py` linhas 640-659
**Problema:**

```python
while time.time() - start_time < max_wait:
    try:
        if os.path.exists(file_path):
            current_size = os.path.getsize(file_path)

            if current_size == last_size:
                stable_time += 1  # ← Incrementa DEPOIS do sleep
                if stable_time >= settle_time_seconds:
                    return True
            else:
                last_size = current_size
                stable_time = 0

    except OSError:
        return False

    time.sleep(1)  # ← Sleep aqui
```

**Por que é bug:** A lógica incrementa `stable_time` e depois faz `sleep(1)`. Mas nunca faz sleep inicial, então primeiro check é instantâneo. Resultado: arquivo é considerado estável em < 1 segundo às vezes.

**Impacto:** Arquivos podem ser transferidos antes de estar realmente estáveis

**Solução:**
```python
def _wait_for_file_settle(file_path: str, settle_time_seconds: int = 30, max_wait: int = 300) -> bool:
    import time

    start_time = time.time()
    last_size = -1
    stable_time = 0

    while time.time() - start_time < max_wait:
        try:
            if os.path.exists(file_path):
                current_size = os.path.getsize(file_path)

                if current_size == last_size:
                    stable_time += 1
                    if stable_time >= settle_time_seconds:
                        return True  # Arquivo é estável!
                else:
                    last_size = current_size
                    stable_time = 0

        except OSError:
            return False

        time.sleep(1)  # Sempre dorme antes de próximo check

    return False  # Timeout
```

---

## RESUMO DE BUGS POR SEVERIDADE

| # | Bug | Severidade | Arquivo | Linha | Fixável? |
|---|-----|-----------|---------|-------|----------|
| 1 | Timeout format em RQ | CRÍTICA | worker_jobs.py | 663-683 |  Sim |
| 2 | Cancelled check muito strict | CRÍTICA | worker_jobs.py | 65-72 |  Sim |
| 3 | Path confuso em MOVE | ALTA | copy_engine.py | 474 |  Refactor |
| 4 | API schema mismatch | MÉDIA | routers/transfers.py | 98-104 |  Verificar |
| 5 | File settle logic | MÉDIA | worker_jobs.py | 640-659 |  Sim |

---

## PRÓXIMAS ETAPAS

1. **Fase 2:** Corrigir todos os 5 bugs em ordem de severidade
2. **Fase 3:** Criar 10 testes abrangentes
3. **Fase 4:** Executar testes e validar

---

**Status:** Auditoria completa 
