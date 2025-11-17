# ️ Guia de Testes via UI - Localhost

**Objetivo:** Testar transferências via interface Web do Ketter 3.0

**Portas:**
-  **Frontend (React):** http://localhost:3000
-  **API (FastAPI):** http://localhost:8000
-  **PostgreSQL:** localhost:5432
-  **Redis:** localhost:6379

---

##  PASSO 1: Iniciar a Aplicação Completa

```bash
cd /Users/pedroc.ampos/Desktop/Ketter3/Ketter_Repo

# Parar tudo que estava rodando
docker-compose down -v

# Esperar um pouco
sleep 2

# Iniciar stack completo (API, Worker, DB, Redis, FRONTEND)
docker-compose up -d

# Verificar que tudo subiu
docker-compose ps

# Você DEVE ver:
#  ketter-postgres (UP)
#  ketter-redis (UP)
#  ketter-api (UP)
#  ketter-worker (UP)
#  ketter-frontend (UP)

# Esperar 15 segundos para tudo estar pronto
sleep 15
```

---

##  PASSO 2: Preparar Arquivos de Teste

Abra um **novo terminal** e execute:

```bash
# Criar diretórios de teste
mkdir -p /tmp/ketter-test/{source,destination}

# Criar arquivo de teste (100MB para ver progresso)
dd if=/dev/zero of=/tmp/ketter-test/source/video_sample.bin bs=1M count=100

# Criar segundo arquivo (50MB)
dd if=/dev/zero of=/tmp/ketter-test/source/document_sample.bin bs=1M count=50

# Criar arquivo para MOVE test (30MB)
mkdir -p /tmp/ketter-test/source/files_to_move
dd if=/dev/zero of=/tmp/ketter-test/source/files_to_move/archivable.bin bs=1M count=30

# Verificar
echo " Arquivos criados:"
ls -lah /tmp/ketter-test/source/

# Deve mostrar:
# video_sample.bin (100M)
# document_sample.bin (50M)
# files_to_move/archivable.bin (30M)
```

---

##  PASSO 3: Abrir o Navegador e Acessar a UI

1. **Abrir navegador do Mac**
   - Chrome / Safari / Firefox / qualquer um

2. **Ir para:** http://localhost:3000

3. **Você deve ver:**
   - Página inicial do Ketter 3.0
   - Botão grande "Iniciar Transferência"
   - Histórico de transferências vazio (primeira vez)

---

##  TESTE 1: COPY Simples (100MB)

### Via UI:

1. **Clique em "Iniciar Transferência"** ou similar

2. **Preencha os campos:**
   ```
   Caminho Origem:     /tmp/ketter-test/source/video_sample.bin
   Caminho Destino:    /tmp/ketter-test/destination/video_copy.bin
   Modo:               COPY
   ```

3. **Clique em "Iniciar"**

4. **Você deve ver:**
   - Barra de progresso enchendo (0% → 100%)
   - Status mudando: PENDING → PROCESSING → COMPLETED
   - Tempo estimado sendo calculado
   - Checksum sendo verificado

5. **Resultado esperado:**
   ```
    Status: COMPLETED
    Tempo: ~5 segundos (depende do Mac)
    Arquivo copiado: 100MB
    Checksum: SHA-256 validado
   ```

### Verificar no Terminal:
```bash
# Confirmar que arquivo foi copiado
ls -lah /tmp/ketter-test/destination/video_copy.bin

# Deve ter exatamente 100MB
file /tmp/ketter-test/destination/video_copy.bin
```

---

##  TESTE 2: MOVE Completo (30MB + Delete)

### Via UI:

1. **Clique em "Iniciar Transferência"**

2. **Preencha:**
   ```
   Caminho Origem:     /tmp/ketter-test/source/files_to_move/archivable.bin
   Caminho Destino:    /tmp/ketter-test/destination/archivable_moved.bin
   Modo:               MOVE
   ```

3. **Clique em "Iniciar"**

4. **Aguarde completar**

5. **Resultado esperado:**
   ```
    Status: COMPLETED
    Arquivo movido (copiado + DELETADO da origem)
    Origem NOT encontrada
    Destino encontrado com 30MB
   ```

### Verificar no Terminal:
```bash
# ORIGEM deve estar DELETADA
if [ -f /tmp/ketter-test/source/files_to_move/archivable.bin ]; then
  echo " ERRO: Arquivo ainda existe na origem!"
else
  echo " OK: Arquivo foi DELETADO da origem (MOVE funcionou!)"
fi

# DESTINO deve existir
ls -lah /tmp/ketter-test/destination/archivable_moved.bin
```

---

##  TESTE 3: Verificar Histórico de Transferências

### Via UI:

1. **Volte para a tela principal**

2. **Procure por "Histórico" ou "Transferências"**

3. **Você deve ver:**
   - Lista com todas as transferências que fez
   - Data e hora de cada uma
   - Status (COMPLETED, FAILED, etc)
   - Tempo total
   - Tamanho do arquivo

4. **Clique em uma transferência para ver detalhes:**
   - Caminho origem e destino
   - Modo (COPY ou MOVE)
   - Checksum do arquivo
   - Eventos/logs completos
   - Tempo de processamento

---

##  TESTE 4: Verificar Audit Logs (API Direta)

Enquanto a UI está rodando, abra outro terminal e verifique os logs:

```bash
# Ver todas as transferências via API
curl -s http://localhost:8000/transfers | jq '.[] | {id, status, operation_mode, created_at}'

# Esperado:
# [
#   {
#     "id": 1,
#     "status": "COMPLETED",
#     "operation_mode": "copy",
#     "created_at": "2025-11-12T..."
#   },
#   ...
# ]

# Ver logs detalhados de uma transferência (ex: ID=1)
curl -s http://localhost:8000/transfers/1/logs | jq '.[] | {event_type, message, created_at}'

# Esperado ver eventos como:
# - TRANSFER_STARTED
# - TRANSFER_PROGRESS
# - CHECKSUM_VERIFIED
# - TRANSFER_COMPLETED
```

---

##  TESTE 5: ENHANCE #1 - Path Security (Deve ser Bloqueado!)

### Tentar via UI:

1. **Clique em "Iniciar Transferência"**

2. **Tente usar path com traversal:**
   ```
   Caminho Origem:     /tmp/../etc/passwd
   Caminho Destino:    /tmp/test.txt
   Modo:               COPY
   ```

3. **Clique em "Iniciar"**

4. **Resultado esperado:**
   ```
    ERRO EXIBIDO NA UI
   Mensagem: "Path traversal detected" ou similar
   Status: NÃO deve criar transferência
   ```

### Verificar no Terminal:
```bash
# Confirmar que arquivo /etc/passwd NÃO foi tocado
ls -la /etc/passwd
# Deve estar intacto

# Confirmar que NÃO foi criada transferência
curl -s http://localhost:8000/transfers | jq 'length'
# Número de transferências não deve ter aumentado
```

---

##  TESTE 6: ENHANCE #4 - Post-Deletion Verification

### Testar via UI:

1. **Fazer um MOVE normal** (já testou isso)

2. **Verificar que:**
   - Arquivo foi copiado com sucesso
   - Arquivo foi verificado (readable check)
   - Arquivo foi deletado da origem
   - UI mostra "COMPLETED"

3. **Isto valida ENHANCE #4** (post-deletion verification)

---

##  TESTE 7: Performance & Escala

### Testar arquivo grande:

1. **Crie um arquivo maior:**
   ```bash
   dd if=/dev/zero of=/tmp/ketter-test/source/large_file.bin bs=1M count=200
   ```

2. **Via UI, transfira este arquivo**

3. **Observe:**
   - Barra de progresso progredindo
   - Tempo estimado sendo atualizado
   - Velocidade de transferência
   - Se completar com sucesso

4. **Resultado esperado:**
   ```
    200MB transferido com sucesso
    Progresso visual funcionando
    Checksum validado
    Tempo razoável (~10-15 seg no Mac)
   ```

---

##  SCENARIO COMPLETO (Recomendado)

Se quiser fazer um teste completo e realista:

```bash
# Terminal 1: Iniciar docker-compose
cd /Users/pedroc.ampos/Desktop/Ketter3/Ketter_Repo
docker-compose down -v && sleep 2 && docker-compose up -d
sleep 15

# Terminal 2: Preparar arquivos
mkdir -p /tmp/ketter-test/{source,destination}
dd if=/dev/zero of=/tmp/ketter-test/source/file1.bin bs=1M count=100
dd if=/dev/zero of=/tmp/ketter-test/source/file2.bin bs=1M count=50
mkdir -p /tmp/ketter-test/source/folder
dd if=/dev/zero of=/tmp/ketter-test/source/folder/file3.bin bs=1M count=30

# Terminal 3: Abrir navegador
# Safari / Chrome / Firefox
# Ir para: http://localhost:3000

# Agora você pode testar via UI! 
```

---

##  Checklist de Validação

Marque conforme completa os testes:

### Funcionalidade Básica
- [ ] Página de UI carrega (localhost:3000)
- [ ] Botão de iniciar transferência está visível
- [ ] Campo de caminho de origem funciona
- [ ] Campo de caminho de destino funciona
- [ ] Seletor de modo (COPY/MOVE) funciona

### COPY Test
- [ ] Transferência inicia
- [ ] Barra de progresso aparece
- [ ] Status muda para COMPLETED
- [ ] Arquivo aparece em destino
- [ ] Tamanho está correto

### MOVE Test
- [ ] Transferência inicia
- [ ] Arquivo é copiado
- [ ] Arquivo é DELETADO da origem
- [ ] Status mostra COMPLETED
- [ ] Histórico registra como MOVE

### ENHANCE #1 - Security
- [ ] Path traversal é bloqueado
- [ ] Erro é exibido na UI
- [ ] Transferência não é criada

### ENHANCE #4 - Verification
- [ ] MOVE valida arquivo antes de deletar
- [ ] Se arquivo está corrompido, origem não é deletada
- [ ] Logs mostram verificação

### Histórico & Logs
- [ ] Histórico lista todas as transferências
- [ ] Detalhe de transferência mostra logs
- [ ] Audit trail é completo
- [ ] Timestamps estão corretos

### ENHANCE #5 - CORS
- [ ] UI consegue fazer requisições para API (localhost:3000 autorizado)
- [ ] Requisições de localhost:8000 também funcionam

---

##  Troubleshooting

### UI não carrega (localhost:3000 em branco)

```bash
# Verificar se frontend subiu
docker-compose logs frontend

# Pode estar compilando ainda
# Espere mais 20 segundos

# Verificar se API está rodando
curl -s http://localhost:8000/health | jq
```

### Transferência fica em PENDING

```bash
# Worker pode não estar processando
docker-compose logs worker

# Restart worker
docker-compose restart worker

# Esperar 10 segundos
sleep 10

# Tentar nova transferência
```

### Erro "Path outside allowed volumes"

```bash
# Problema: arquivo em path não autorizado
# Solução: usar /tmp/ketter-test como preparado

# Ou se quiser usar outro path, editar:
# docker-compose.yml
# Line 76: - /Users:/Users:cached (já está liberado!)
```

### Arquivo não aparece em destino

```bash
# Verificar logs da transferência
curl -s http://localhost:8000/transfers/1/logs | jq '.'

# Pode ser:
# 1. Permissão de arquivo
# 2. Disco cheio
# 3. Path inválido

# Verificar logs do API
docker-compose logs api | tail -50
```

---

##  O que Validar nos Testes

Durante cada teste, preste atenção em:

1. **Validação de Path** (ENHANCE #1)
   -  Path válido é aceito
   -  Path com `..` é bloqueado
   -  Symlinks em destino são bloqueados

2. **Locks Concorrentes** (ENHANCE #2)
   -  Dois COPYs rodando paralelo (rápido)
   -  Dois MOVEs no mesmo arquivo não podem rodar juntos

3. **Rollback** (ENHANCE #3)
   -  Se falhar, nenhuma alteração fica
   -  Arquivo inválido não é deixado em destino

4. **Verification** (ENHANCE #4)
   -  MOVE valida arquivo antes de deletar origem
   -  Se arquivo está corrompido, avisa

5. **CORS** (ENHANCE #5)
   -  UI consegue chamar API
   -  localhost:3000 autorizado

6. **Circuit Breaker** (ENHANCE #6)
   -  Watch mode (se usar) tem proteção contra runaway

---

##  Exemplo de Tela Esperada

### Tela de Inicio (localhost:3000)
```
┌─────────────────────────────────────┐
│         KETTER 3.0                  │
│    Reliable File Transfer           │
├─────────────────────────────────────┤
│                                     │
│  [Iniciar Transferência]            │
│                                     │
│  Histórico de Transferências:       │
│  ┌─────────────────────────────────┐│
│  │ ID │ Status │ Tamanho │ Tempo  ││
│  │ 1  │ DONE │ 100 MB  │ 5 seg  ││
│  │ 2  │ DONE │ 50 MB   │ 3 seg  ││
│  │ 3  │ DONE │ 30 MB   │ 2 seg  ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### Tela de Transferência (em progresso)
```
┌─────────────────────────────────────┐
│    Transferência #4                 │
├─────────────────────────────────────┤
│ Origem: /tmp/ketter-test/source/... │
│ Destino: /tmp/ketter-test/dest/...  │
│ Modo: COPY                          │
│                                     │
│ Progresso: [████████░░] 75%        │
│ Tempo: 7.5 seg / ~10 seg estimado   │
│ Velocidade: 13.3 MB/s              │
│                                     │
│ Status: PROCESSING                  │
│ Checksum: Validando...              │
│                                     │
│              [Cancelar]             │
└─────────────────────────────────────┘
```

---

## ⏱️ Tempo Total

- **Setup:** 5 min (docker-compose)
- **Preparar arquivos:** 3 min
- **Testes básicos:** 10 min
- **Testes completos:** 15-20 min

**Total: 30-40 minutos**

---

##  Conclusão

Se todos esses testes passarem na UI:

 Frontend funciona
 API funciona
 Worker processa transferências
 Segurança está ativa
 Audit logs registram tudo
 **VOCÊ PODE FAZER A PR COM CONFIANÇA! **

---

**Bom teste! Deixe-me saber se encontrar qualquer problema.** 
