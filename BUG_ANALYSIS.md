# Bug Analysis - Watch Mode Transfer System

## BUGS ENCONTRADOS (Análise Senior)

### BUG #1: Watch Progress Callback com Sessão DB Inválida
**Localização:** `app/worker_jobs.py:184-192` na função `watch_and_transfer_job()`

**Código Problemático:**
```python
def watch_progress(elapsed, max_wait, checks_done):
    log = AuditLog(...)
    db.add(log)  # <-- BUG: db sessão pode estar fechada/inválida
    db.commit()
```

**Problema:**
- A função `watch_progress()` é usada como callback dentro de `watch_folder_until_stable()`
- Ela tenta adicionar log na sessão `db`
- MAS a sessão pode ter sido reusada ou commit() em outra parte pode ter causado problemas
- Tenta usar `db` que está definido no escopo externo (closure)

**Impacto:** Possível erro silencioso ou exceção durante watch

**Solução:** Remover callback ou redesenhar para não usar DB na callback

---

### BUG #2: Transferência Marcada como FAILED Prematuramente
**Localização:** Fluxo geral entre API e Worker

**Problema:**
- Quando transfer é criada com `watch_continuous=True`
- A transferência original fica em status PENDING
- Mas a lógica do continuous watcher marca a transferência PAI como FAILED quando alguém clica "Stop"
- Isso impede novos jobs de serem enfileirados

**Impacto:** Transfer 119 mostra "FAILED" e "Transfer cancelled by user" mas ninguém cancelou

**Solução:** Separar transferência de "watch metadata" da transferência real

---

### BUG #3: Ordem Incorreta de MOVE Delete vs Unzip
**Localização:** `app/copy_engine.py:438-465`

**Código Problemático:**
```python
# Linha 438-450: PRIMEIRO delete
if transfer.operation_mode == "move":
    delete_source_after_move(...)  # DELETA SOURCE

# Linha 453-465: DEPOIS unzip
if is_folder:
    unzip_folder_smart(dest_for_copy, ...)  # Se falhar, source já foi deletado!
```

**Problema:**
- Se operação é MOVE + FOLDER
- Primeiro delete a source
- Depois tenta fazer unzip na destination
- Se unzip falhar = perda de dados (source deletado, destination incompleto)

**Impacto:** Integridade de dados comprometida em caso de erro

**Solução:** Fazer unzip ANTES de delete, ou fazer delete ao final

---

### BUG #4: Watch Folder com Pasta Pré-existente
**Localização:** `app/watch_folder.py:139-223` função `watch_folder_until_stable()`

**Problema:**
```python
# Linha 180: Pega estado inicial (pasta com 4 arquivos)
previous_state = get_folder_state(folder_path)  # {4 arquivos}

# Linha 191: Espera 30s
time.sleep(settle_time_seconds)

# Linha 206: Pega estado novo (ainda 4 arquivos)
current_state = get_folder_state(folder_path)  # {4 arquivos}

# Linha 209: Compara
is_stable = compare_folder_states(previous_state, current_state)  # True!

# Retorna True IMEDIATAMENTE (não realmente esperou 30s)
```

**Impacto:** Se pasta já tiver arquivos quando watch começa, transferência dispara em 30s sem realmente saber que ficou estável por 30s

**Nota:** Tecnicamente pode estar correto dependendo de interpretação, mas é potencialmente confuso

---

### BUG #5: Não Há Feedback Visual de Status em Tempo Real
**Localização:** Fluxo geral da transferência

**Problema:**
- Frontend faz polling a cada 2s
- Mas transfer status não é atualizado durante watch
- Usuário vê "PENDING" por 30+ segundos
- Não sabe se está funcionando ou travado

**Impacto:** Péssima experiência do usuário

---

### BUG #6: Watch Progress Callback Assinatura Errada
**Localização:** `app/watch_folder.py:203` vs `app/worker_jobs.py:184`

**Código em watch_folder.py (linha 203):**
```python
progress_callback(elapsed, settle_time_seconds, state_info)
```

**Código em worker_jobs.py (linhas 184):**
```python
def watch_progress(elapsed, max_wait, checks_done):
```

**Problema:**
- watch_folder chama callback com (elapsed, settle_time, dict)
- worker_jobs define callback com (elapsed, max_wait, checks_done)
- Mismatch! O `dict` é recebido como `checks_done`
- Depois tenta usar `checks_done` que é um dict, não um int!

**Impacto:** Erro quando tenta acessar `checks_done` como inteiro

---

## RECOMENDAÇÕES (Dev Senior)

1. **Separar Watch Metadata da Transfer**
   - Criar tabela `WatchSession` para rastrear watch operations
   - Transfer fica apenas para transferências reais

2. **Reordenar MOVE Logic**
   ```python
   # 1. Unzip primeiro (se folder)
   if is_folder:
       unzip_folder_smart(...)

   # 2. Delete segundo (só depois de sucesso)
   if transfer.operation_mode == "move":
       delete_source_after_move(...)
   ```

3. **Remover DB Access da Watch Callback**
   - Callback deve ser pure function (sem side effects)
   - Logging deve ser feito FORA do watch loop

4. **Consertar Assinatura de Callback**
   - Padronizar callback signature
   - Documentar claramente parâmetros

5. **Adicionar Status "WATCHING"**
   - Quando watch_mode ativo, status = "WATCHING"
   - Quando estável, muda para "COPYING"
   - Assim usuário vê progresso

6. **Adicionar Timeout Checker**
   - Se transfer em PENDING > 1 hora = mark as FAILED
   - Evita transferências esquecidas

---

## CHECKLIST DE FIX

- [ ] Fix callback signature mismatch
- [ ] Reorder MOVE delete (unzip first, delete second)
- [ ] Add "WATCHING" status
- [ ] Separate watch metadata from transfer
- [ ] Add timeout detection
- [ ] Test complete watch -> transfer -> move flow
- [ ] Test folder transfer + move mode
