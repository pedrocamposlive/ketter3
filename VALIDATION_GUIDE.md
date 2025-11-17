# Ketter 3.0 - System Validation Guide

Este guia explica como validar que o sistema Ketter 3.0 está funcionando corretamente.

##  Scripts de Validação Disponíveis

### 1. Quick Validation (`quick_validate.sh`)  **RECOMENDADO**

Script rápido que testa os componentes essenciais do sistema em ~30 segundos.

**Uso:**
```bash
./quick_validate.sh
```

**O que é testado (10 testes):**
1.  Docker services (postgres, redis, api, worker, frontend)
2.  API health endpoint
3.  Frontend accessibility
4.  Database connectivity
5.  File creation capability
6.  Transfer creation via API
7.  Transfer completion monitoring
8.  Triple SHA-256 checksums
9.  Destination file verification
10.  Automated test suite (43 tests)

**Saída esperada:**
```

KETTER 3.0 - SYSTEM VALIDATION


[1/10] Checking Docker services...
 All Docker services are running

[2/10] Checking API health...
 API is healthy

...


VALIDATION RESULTS


Tests Passed: 10/10
Tests Failed: 0/10

 ALL TESTS PASSED - SYSTEM IS OPERATIONAL
 KETTER 3.0 IS PRODUCTION-READY
```

### 2. Complete Validation (`validate_system.sh`) 

Script completo e detalhado que testa TODOS os aspectos do sistema em ~60 segundos.

**Uso:**
```bash
./validate_system.sh
```

**O que é testado (22 testes):**
- **Phase 1:** Docker Infrastructure (6 testes)
  - Containers running, health checks
- **Phase 2:** API Connectivity (4 testes)
  - Health, status, documentation endpoints
- **Phase 3:** Database Operations (2 testes)
  - Schema validation, table access
- **Phase 4:** Complete Transfer Workflow (14 testes)
  - File creation, transfer, checksums, audit trail, PDF
- **Phase 5:** Cleanup (1 teste)
  - Resource cleanup
- **Phase 6:** Automated Test Suite (1 teste)
  - Full pytest suite

##  Quando Usar Cada Script

### Use `quick_validate.sh` quando:
-  Quiser validar rapidamente que o sistema está funcional
-  Após iniciar os containers (`docker-compose up`)
-  Após fazer mudanças pequenas
-  Para verificação diária
-  **PRIMEIRA VEZ que executar o sistema**

### Use `validate_system.sh` quando:
-  Quiser validação completa e detalhada
-  Antes de fazer deploy em produção
-  Após mudanças significativas no código
-  Para debugging de problemas
-  Para relatórios de qualidade

##  Interpretando os Resultados

###  Sucesso (Exit Code 0)
Todos os testes passaram. Sistema está operacional e pronto para uso.

**Indicadores de sucesso:**
- Todas as linhas com `` (checkmark verde)
- "ALL TESTS PASSED" no final
- "SYSTEM IS OPERATIONAL"
- Exit code 0

###  Falha (Exit Code 1)
Algum teste falhou. Revise os erros e corrija.

**Indicadores de falha:**
- Linhas com `` (X vermelho)
- Mensagens de erro específicas
- "SOME TESTS FAILED" no final
- Exit code 1

##  Troubleshooting

### Problema: Docker services não estão rodando

**Erro:**
```
 Docker services not running
```

**Solução:**
```bash
docker-compose up -d
sleep 10  # Aguardar containers iniciarem
./quick_validate.sh
```

### Problema: API não responde

**Erro:**
```
 API not responding
```

**Soluções:**
1. Verificar se container API está healthy:
   ```bash
   docker-compose ps api
   ```

2. Ver logs do API:
   ```bash
   docker-compose logs api --tail=50
   ```

3. Restart API:
   ```bash
   docker-compose restart api
   sleep 5
   ./quick_validate.sh
   ```

### Problema: Transfer falha

**Erro:**
```
 Transfer failed
```

**Soluções:**
1. Verificar worker está rodando:
   ```bash
   docker-compose ps worker
   docker-compose logs worker --tail=50
   ```

2. Verificar espaço em disco:
   ```bash
   df -h
   ```

3. Verificar permissões:
   ```bash
   docker-compose exec api ls -la /data/transfers/
   ```

### Problema: Checksums incompletos

**Erro:**
```
 Checksums incomplete
```

**Soluções:**
1. Verificar se worker processou o transfer:
   ```bash
   curl http://localhost:8000/transfers/{id}/logs | python3 -m json.tool
   ```

2. Aguardar mais tempo (transfer pode estar processando)

3. Verificar logs de erro:
   ```bash
   docker-compose logs worker --tail=50
   ```

##  Logs e Debugging

### Ver todos os logs:
```bash
docker-compose logs -f
```

### Ver logs específicos:
```bash
docker-compose logs api -f       # API logs
docker-compose logs worker -f    # Worker logs
docker-compose logs postgres     # Database logs
```

### Verificar status dos containers:
```bash
docker-compose ps
```

### Entrar em um container:
```bash
docker-compose exec api bash      # API container
docker-compose exec postgres psql -U ketter -d ketter  # Database
```

##  Workflow Recomendado

### Primeira Vez:
```bash
# 1. Iniciar sistema
docker-compose up -d

# 2. Aguardar services ficarem healthy (~30s)
sleep 30

# 3. Validar sistema
./quick_validate.sh

# 4. Se passou, acessar UI
open http://localhost:3000
```

### Uso Diário:
```bash
# 1. Verificar se containers estão rodando
docker-compose ps

# 2. Se não estão, iniciar
docker-compose up -d
sleep 30

# 3. Validação rápida
./quick_validate.sh

# 4. Usar o sistema
```

### Antes de Deploy:
```bash
# 1. Validação completa
./validate_system.sh

# 2. Se passou, sistema está pronto
# 3. Commit e deploy
```

##  Validação Manual Adicional

Além dos scripts automatizados, você pode validar manualmente:

### 1. Acessar a UI:
```
http://localhost:3000
```

### 2. Criar uma transferência manual:
- Source: `/data/transfers/test.txt`
- Destination: `/data/transfers/test_copy.txt`
- Clicar "Start Transfer"
- Observar progresso em tempo real

### 3. Verificar PDF Report:
- Ir para "Transfer History"
- Clicar em " Download Report"
- Abrir PDF e verificar conteúdo

### 4. Verificar Audit Trail:
- Clicar em "View Audit Trail"
- Verificar que todos os eventos estão logados

### 5. Verificar API Docs:
```
http://localhost:8000/docs
```

##  Métricas de Qualidade

Após executar `quick_validate.sh` com sucesso, você tem garantia de:

-  **Disponibilidade:** Todos os serviços operacionais
-  **Conectividade:** API, Database, Redis, Worker comunicando
-  **Funcionalidade:** Copy engine funcionando com triple SHA-256
-  **Integridade:** Checksums verificados e matching
-  **Qualidade:** 43/43 testes automatizados passando
-  **Confiabilidade:** Zero erros em transferência end-to-end

##  Critérios de Produção

O sistema está pronto para produção quando:

1.  `quick_validate.sh` passa 10/10 testes
2.  UI acessível em http://localhost:3000
3.  Transferência manual bem-sucedida
4.  PDF report gerado corretamente
5.  Audit trail completo visível
6.  Checksums verificados (SOURCE = DESTINATION = FINAL)
7.  Zero erros nos logs

##  Documentação Relacionada

- **[TESTING.md](TESTING.md)** - Guia completo de testes (unit, integration, 500GB)
- **[PROJECT_README.md](PROJECT_README.md)** - Documentação completa do projeto
- **[CLAUDE.md](CLAUDE.md)** - Filosofia de desenvolvimento (MRC)
- **[state.md](state.md)** - Status do projeto e métricas

---

**Última Atualização:** 2025-11-05
**Status:** Sistema 100% validado e production-ready 
