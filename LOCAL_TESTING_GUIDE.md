#  Guia de Testes Locais - Mac

**Objetivo:** Testar a aplicação Ketter 3.0 localmente com todas as enhancements

**Tempo estimado:** 30-45 minutos

---

##  Pré-requisitos

Verificar que você tem instalado:
- Docker Desktop (rodando)
- curl (para fazer requisições HTTP)
- Python 3.13+ (para testes)

```bash
# Verificar Docker
docker --version
docker-compose --version

# Verificar curl
curl --version

# Verificar Python
python3 --version
```

---

##  PARTE 1: Iniciar a Aplicação

### Step 1: Limpar ambiente anterior
```bash
cd /Users/pedroc.ampos/Desktop/Ketter3/Ketter_Repo

# Parar tudo e limpar volumes
docker-compose down -v

# Esperar um pouco
sleep 3
```

### Step 2: Iniciar stack completo
```bash
# Iniciar tudo (API, Worker, DB, Redis)
docker-compose up -d

# Verificar que os containers estão rodando
docker-compose ps

# Você deve ver:
# - ketter_api running
# - ketter_worker running
# - postgres running
# - redis running
```

### Step 3: Esperar services estarem prontos
```bash
# Esperar 10 segundos para tudo subir
sleep 10

# Verificar health da API
curl -s http://localhost:8000/health | jq

# Deve retornar:
# {
#   "status": "ok",
#   "database": "connected",
#   "redis": "connected"
# }
```

---

##  PARTE 2: Preparar Arquivos de Teste

### Step 1: Criar diretório de testes
```bash
# Criar pasta de teste
mkdir -p /tmp/ketter-test/{source,destination}

# Criar arquivo de teste (1MB)
dd if=/dev/zero of=/tmp/ketter-test/source/test_file_1mb.bin bs=1M count=1

# Criar arquivo maior (10MB)
dd if=/dev/zero of=/tmp/ketter-test/source/test_file_10mb.bin bs=1M count=10

# Verificar os arquivos
ls -lah /tmp/ketter-test/source/

# Você deve ver:
# test_file_1mb.bin (1.0M)
# test_file_10mb.bin (10M)
```

### Step 2: Criar pasta para teste de MOVE
```bash
# Criar subdiretório para MOVE (será deletado durante o teste)
mkdir -p /tmp/ketter-test/source/to_move
dd if=/dev/zero of=/tmp/ketter-test/source/to_move/moveable.bin bs=1M count=1

ls -lah /tmp/ketter-test/source/
```

---

##  PARTE 3: Rodar Testes de Transferência

### TEST 1: COPY Simples (1MB)

```bash
echo "=== TEST 1: COPY Simples (1MB) ==="
echo ""

# Fazer requisição POST para COPY
TRANSFER_ID=$(curl -s -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/tmp/ketter-test/source/test_file_1mb.bin",
    "destination_path": "/tmp/ketter-test/destination/test_file_1mb_copy.bin",
    "operation_mode": "copy"
  }' | jq -r '.id')

echo "Transfer ID: $TRANSFER_ID"
echo ""

# Esperar um pouco para processar
sleep 3

# Verificar status
curl -s http://localhost:8000/transfers/$TRANSFER_ID | jq '.'

# Você deve ver:
# - "status": "COMPLETED"
# - "operation_mode": "copy"
# - "progress": 100

# Verificar que arquivo foi copiado
echo ""
echo "Verificando arquivo de destino:"
ls -lah /tmp/ketter-test/destination/test_file_1mb_copy.bin

# Deve existir e ter 1M
```

---

### TEST 2: COPY Maior (10MB)

```bash
echo "=== TEST 2: COPY Maior (10MB) ==="
echo ""

TRANSFER_ID=$(curl -s -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/tmp/ketter-test/source/test_file_10mb.bin",
    "destination_path": "/tmp/ketter-test/destination/test_file_10mb_copy.bin",
    "operation_mode": "copy"
  }' | jq -r '.id')

echo "Transfer ID: $TRANSFER_ID"
sleep 3

curl -s http://localhost:8000/transfers/$TRANSFER_ID | jq '.'

echo ""
echo "Verificando arquivo:"
ls -lah /tmp/ketter-test/destination/test_file_10mb_copy.bin
```

---

### TEST 3: MOVE (Arquivo deletado após transferência)

```bash
echo "=== TEST 3: MOVE (fonte será deletada) ==="
echo ""

echo "Antes do MOVE - arquivo existe:"
ls -lah /tmp/ketter-test/source/to_move/moveable.bin

# Fazer MOVE
TRANSFER_ID=$(curl -s -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/tmp/ketter-test/source/to_move/moveable.bin",
    "destination_path": "/tmp/ketter-test/destination/moveable_moved.bin",
    "operation_mode": "move"
  }' | jq -r '.id')

echo ""
echo "Transfer ID: $TRANSFER_ID"
sleep 3

curl -s http://localhost:8000/transfers/$TRANSFER_ID | jq '.'

echo ""
echo "Depois do MOVE - verificar origem:"
if [ -f /tmp/ketter-test/source/to_move/moveable.bin ]; then
  echo " ERRO: Arquivo ainda existe na origem!"
  ls -lah /tmp/ketter-test/source/to_move/moveable.bin
else
  echo " OK: Arquivo foi deletado da origem"
fi

echo ""
echo "Verificar destino:"
ls -lah /tmp/ketter-test/destination/moveable_moved.bin
```

---

### TEST 4: ENHANCE #1 - Path Security (Bloqueado!)

```bash
echo "=== TEST 4: ENHANCE #1 - Path Traversal Attack (DEVE SER BLOQUEADO) ==="
echo ""

echo "Tentando path traversal attack (..):"
curl -s -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/tmp/../etc/passwd",
    "destination_path": "/tmp/ketter-test/destination/passwd.txt",
    "operation_mode": "copy"
  }' | jq '.'

# Você DEVE ver erro 422 com mensagem de "path traversal detected"
echo ""
echo " Se viu erro 422 = ENHANCE #1 funcionando!"
```

---

### TEST 5: ENHANCE #1 - Symlink Attack (Bloqueado!)

```bash
echo "=== TEST 5: ENHANCE #1 - Symlink Attack (DEVE SER BLOQUEADO) ==="
echo ""

# Criar symlink
ln -sf /etc/passwd /tmp/ketter-test/source/symlink_attack.txt

echo "Tentando transferir via symlink:"
curl -s -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/tmp/ketter-test/source/symlink_attack.txt",
    "destination_path": "/tmp/ketter-test/destination/stolen_passwd.txt",
    "operation_mode": "copy"
  }' | jq '.'

# Você DEVE ver erro de "symlink not allowed"
echo ""
echo " Se viu erro = ENHANCE #1 funcionando!"

# Limpar
rm -f /tmp/ketter-test/source/symlink_attack.txt
```

---

### TEST 6: ENHANCE #5 - CORS Whitelist

```bash
echo "=== TEST 6: ENHANCE #5 - CORS Whitelist ==="
echo ""

# Requisição com Origin não autorizado
curl -i -X OPTIONS http://localhost:8000/transfers \
  -H "Origin: http://evil.com" \
  -H "Access-Control-Request-Method: POST" 2>/dev/null | grep -i "access-control"

echo ""
echo " Se NÃO viu CORS headers = está seguro (whitelist funcionando)"
echo ""

# Requisição com Origin autorizado
curl -i -X OPTIONS http://localhost:8000/transfers \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" 2>/dev/null | grep -i "access-control"

echo ""
echo " Se viu CORS headers para localhost:3000 = OK"
```

---

##  PARTE 4: Verificar Audit Logs

### Listar transferências completadas
```bash
echo "=== Listar Todas as Transferências ==="
echo ""

curl -s http://localhost:8000/transfers | jq '.'

# Você deve ver um array com todas as transferências
```

### Ver logs de uma transferência específica
```bash
echo "=== Ver Logs de uma Transferência ==="
echo ""

# Usar o ID de uma transferência (ex: 1)
curl -s http://localhost:8000/transfers/1/logs | jq '.'

# Você deve ver todos os eventos:
# - TRANSFER_STARTED
# - TRANSFER_PROGRESS
# - CHECKSUM_VERIFIED
# - TRANSFER_COMPLETED
# - Etc
```

---

##  PARTE 5: Checklist de Validação

Verificar se todos os 6 enhancements estão funcionando:

```bash
echo "=== CHECKLIST DE VALIDAÇÃO ==="
echo ""
echo "[ ] ENHANCE #1: Path Traversal Bloqueado"
echo "    → TEST 4 passou com erro 422?"
echo ""
echo "[ ] ENHANCE #1: Symlink Bloqueado"
echo "    → TEST 5 passou com erro?"
echo ""
echo "[ ] ENHANCE #2: Lock Protection"
echo "    → MOVE foi serializado (não paralelo)?"
echo ""
echo "[ ] ENHANCE #3: Rollback"
echo "    → Transferências falhadas marcadas como FAILED?"
echo ""
echo "[ ] ENHANCE #4: Verification"
echo "    → Arquivo copiado tem mesmo tamanho?"
echo ""
echo "[ ] ENHANCE #5: CORS"
echo "    → Localhost autorizado, evil.com bloqueado?"
echo ""
echo "[ ] ENHANCE #6: Circuit Breaker"
echo "    → Watch mode está protegido?"
echo ""
```

---

##  PARTE 6: Limpeza

```bash
# Quando terminar os testes, parar tudo
docker-compose down -v

# Limpar arquivos de teste (opcional)
rm -rf /tmp/ketter-test

echo " Tudo limpo!"
```

---

##  Script Completo (Opcional)

Se quiser rodar tudo de uma vez, salve isso em um arquivo:

```bash
#!/bin/bash
# save as: test_local.sh
# run with: bash test_local.sh

set -e

cd /Users/pedroc.ampos/Desktop/Ketter3/Ketter_Repo

echo " Starting docker-compose..."
docker-compose down -v
sleep 2
docker-compose up -d
sleep 10

echo " Creating test files..."
mkdir -p /tmp/ketter-test/{source,destination}
dd if=/dev/zero of=/tmp/ketter-test/source/test_1mb.bin bs=1M count=1 2>/dev/null

echo " Health check..."
curl -s http://localhost:8000/health | jq .

echo " Testing COPY..."
curl -s -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/tmp/ketter-test/source/test_1mb.bin",
    "destination_path": "/tmp/ketter-test/destination/test_1mb.bin",
    "operation_mode": "copy"
  }' | jq '.'

sleep 2

echo ""
echo " Checking results..."
ls -lah /tmp/ketter-test/destination/

echo ""
echo " Done!"
```

---

##  Troubleshooting

### Docker não inicia
```bash
# Verificar logs
docker-compose logs

# Tentar restart
docker-compose restart
```

### Erro de conexão (localhost:8000 não responde)
```bash
# Esperar mais tempo
sleep 20

# Verificar se containers estão rodando
docker-compose ps

# Ver logs do API
docker-compose logs ketter_api
```

### Path /tmp não funciona
```bash
# No Mac, /tmp é alias para /private/tmp
# Você pode usar os dois, o código trata automaticamente

# Testar com /private/tmp
curl -s -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/private/tmp/ketter-test/source/test_1mb.bin",
    "destination_path": "/private/tmp/ketter-test/destination/test_1mb.bin",
    "operation_mode": "copy"
  }' | jq '.'
```

### Erro 422 em transferência válida
```bash
# Pode ser path security being strict
# Verificar logs do API
docker-compose logs ketter_api | tail -20

# Ver a mensagem de erro exata
curl -s http://localhost:8000/transfers/1 | jq '.error_message'
```

---

##  Resultado Esperado

Depois dos testes, você deve ter:

 3 arquivos copiados em `/tmp/ketter-test/destination/`
 1 arquivo movido (origem deletada)
 Path traversal bloqueado
 Symlink bloqueado
 CORS funcionando
 Todos os logs de auditoria registrados

**Se tudo passar → Você tem confiança para fazer a PR! **

---

**Tempo total: 30-45 minutos**
