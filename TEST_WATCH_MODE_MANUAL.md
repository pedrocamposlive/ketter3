# Manual Test Guide - Watch Mode Fixes

## Bugs Corrigidos

### 1. Callback Signature Mismatch (BUG #6) 
- **Antes:** watch_progress() recebia (elapsed, max_wait, checks_done) mas checks_done era um dict
- **Depois:** watch_progress() agora recebe corretamente (elapsed, settle_time, state_info)

### 2. Reordenação MOVE Delete (BUG #3) 
- **Antes:** Delete source → Unzip → Se falhar = perda de dados
- **Depois:** Unzip → Delete source → Safer order

### 3. DB Access em Callback (BUG #1) 
- **Antes:** Callback tentava acessar db.add() e db.commit()
- **Depois:** Callback apenas loga, DB é atualizado após watch completo

---

## Teste Manual: Passo a Passo

### Setup
```bash
# Limpar pasta de testes
rm -rf /Users/pedroc.ampos/Desktop/OUT/*
rm -rf /Users/pedroc.ampos/Desktop/IN/*

# Criar 3-4 arquivos de teste
echo "File 1" > /Users/pedroc.ampos/Desktop/OUT/test1.txt
echo "File 2" > /Users/pedroc.ampos/Desktop/OUT/test2.txt
echo "File 3" > /Users/pedroc.ampos/Desktop/OUT/test3.txt
```

### Teste 1: Watch Mode - 30 Segundos
**Objetivo:** Verificar se watch espera corretamente e depois transfere

1. Abrir http://localhost:3000
2. Clicar "Create New Transfer"
3. Preencher:
   - **Source:** `/Users/pedroc.ampos/Desktop/OUT`
   - **Destination:** `/Users/pedroc.ampos/Desktop/IN`
   - **Watch Mode:**  (marcar)
   - **Settle Time:** 30 segundos
   - **Operation:** COPY (manter padrão)
4. Clicar "Create Transfer"

**Esperado:**
-  Transferência aparece com status "PENDING"
-  Passar 30 segundos de watch
-  Log do worker mostra: "Folder stable after 30s..."
-  Arquivos aparecem em `/Users/pedroc.ampos/Desktop/IN`
-  Arquivos ainda existem em `OUT` (COPY mode)

**Verificar logs:**
```bash
docker-compose logs worker --tail=20 | grep -i "stable\|watch\|progress"
```

---

### Teste 2: MOVE Mode - Delete Source
**Objetivo:** Verificar se MOVE mode deleta corretamente a source

1. Limpar pastas novamente:
   ```bash
   rm -rf /Users/pedroc.ampos/Desktop/OUT/*
   rm -rf /Users/pedroc.ampos/Desktop/IN/*
   echo "File A" > /Users/pedroc.ampos/Desktop/OUT/fileA.txt
   echo "File B" > /Users/pedroc.ampos/Desktop/OUT/fileB.txt
   ```

2. Criar transferência:
   - **Source:** `/Users/pedroc.ampos/Desktop/OUT`
   - **Destination:** `/Users/pedroc.ampos/Desktop/IN`
   - **Watch Mode:**  (marcar)
   - **Settle Time:** 30
   - **Operation:** MOVE ← IMPORTANTE!
3. Clicar "Create Transfer"
4. **ESPERAR 30 SEGUNDOS + tempo de transferência**

**Esperado:**
-  Após conclusão: `OUT` folder é **preservado mas vazio**
-  `IN` folder contém os arquivos
-  Log mostra: "Unzipping folder..." → "Deleting source..."
-  Não há erro "failed to delete"

**Verificar:**
```bash
# Deve estar vazio
ls -la /Users/pedroc.ampos/Desktop/OUT

# Deve ter os arquivos
ls -la /Users/pedroc.ampos/Desktop/IN
```

---

### Teste 3: Folder Transfer + MOVE Mode
**Objetivo:** Testar transferência de PASTA com MOVE mode

1. Criar estrutura:
   ```bash
   rm -rf /Users/pedroc.ampos/Desktop/OUT/*
   mkdir -p /Users/pedroc.ampos/Desktop/OUT/subfolder
   echo "Root file" > /Users/pedroc.ampos/Desktop/OUT/root.txt
   echo "Nested file" > /Users/pedroc.ampos/Desktop/OUT/subfolder/nested.txt
   ```

2. Criar transferência:
   - **Source:** `/Users/pedroc.ampos/Desktop/OUT` (folder!)
   - **Destination:** `/Users/pedroc.ampos/Desktop/IN`
   - **Watch:** 
   - **Settle:** 30
   - **Operation:** MOVE
3. Clicar "Create Transfer"

**Esperado:**
-  Status muda: PENDING → VALIDATING → COPYING → VERIFYING → COMPLETED
-  Log mostra: "Zipping folder..." → "Unzipping folder..." → "Deleting source..."
-  `OUT` folder é preservado mas vazio
-  `IN` contém pasta descompactada com mesma estrutura

**Verificar:**
```bash
# Estrutura em IN deve ser idêntica
find /Users/pedroc.ampos/Desktop/IN -type f
```

---

### Teste 4: Watch Mode - Continuous (Permanent)
**Objetivo:** Testar modo contínuo que monitora permanentemente

1. Criar transferência:
   - **Source:** `/Users/pedroc.ampos/Desktop/OUT`
   - **Destination:** `/Users/pedroc.ampos/Desktop/IN`
   - **Watch Mode:** 
   - **Continuous Watch:**  ← NOVO!
   - **Settle:** 30
2. Clicar "Create Transfer"

3. **Primeira transferência:**
   - Adicionar arquivo em OUT
   - Esperar 30 segundos
   - Arquivo deve aparecer em IN

4. **Segunda transferência (sem parar o job):**
   - Adicionar NOVO arquivo em OUT
   - Esperar 30 segundos
   - Novo arquivo deve aparecer em IN

**Esperado:**
-  Transferência 1 aparece e completa
-  Transferência 1 fica em histórico
-  Transferência 2 é criada automaticamente para arquivo novo
-  Sistema continua monitorando

---

## Checklist de Validação

- [ ] Watch mode espera 30s corretamente
- [ ] Pasta é preservada em MOVE mode
- [ ] Conteúdo é deletado em MOVE mode
- [ ] Folder transfer cria ZIP e extrai
- [ ] Checksums são calculados (SOURCE, DESTINATION, FINAL)
- [ ] Audit trail mostra todos os passos
- [ ] Logs mostram progresso (não travado)
- [ ] Continuous watch detecta múltiplos arquivos
- [ ] Sem erros de "cannot access" ou "permission denied"
- [ ] Sem erros de "Transfer cancelled by user" não solicitado

---

## Verificar Logs

```bash
# Ver últimas operações do worker
docker-compose logs worker --tail=50

# Procurar por erros específicos
docker-compose logs worker | grep -i "error\|failed\|exception"

# Ver apenas operações de watch
docker-compose logs worker | grep -i "watch\|stable\|settle"
```

---

## Rollback (Se algo der errado)

```bash
# Se precisar reverter as mudanças
git diff HEAD

# Reverter um arquivo específico
git checkout app/worker_jobs.py

# Restart containers
docker-compose restart
```
