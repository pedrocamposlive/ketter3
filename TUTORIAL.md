# Tutorial Passo-a-Passo: Implementando o Sistema Multi-Agente

Este guia mostra exatamente como implementar e executar o sistema multi-agente para construir o Ketter 3.0.

---

##  Pré-requisitos

```bash
# 1. Python 3.11+
python --version  # Deve ser >= 3.11

# 2. Docker e Docker Compose
docker --version
docker-compose --version

# 3. (Opcional) Claude Code
# Se quiser automação completa
# Instale via: https://claude.ai/code
```

---

##  Parte 1: Setup Inicial (5 minutos)

### Passo 1: Criar Estrutura do Projeto

```bash
# 1. Criar diretório do projeto
mkdir ketter-3.0-multiagent
cd ketter-3.0-multiagent

# 2. Criar estrutura básica
mkdir -p {logs,tests,app,worker,frontend}

# 3. Copiar arquivos fornecidos
# - CLAUDE.md (você já tem)
# - orchestrator.py
# - claude_code_agents.py
# - state.md (template inicial)
```

### Passo 2: Instalar Dependências Python

```bash
# Criar requirements.txt
cat > requirements.txt << 'EOF'
# Multi-Agent System
dataclasses-json==0.6.3

# Para agentes avançados (opcional)
crewai==0.1.0
langchain==0.1.0

# Dependências do Ketter (para quando agentes criarem código)
fastapi==0.109.0
uvicorn==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
redis==5.0.1
rq==1.16.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
EOF

# Instalar
pip install -r requirements.txt
```

### Passo 3: Validar Setup

```bash
# Testar que orchestrator funciona
python orchestrator.py

# Output esperado:
#  Ketter 3.0 Multi-Agent Orchestrator
#  WEEK 1 - Copy 1 file with checksum verification
# ...
```

---

##  Parte 2: Execução Manual (Opção 1) - 30 minutos

### Passo 1: Inicializar State

```bash
# Executar orchestrator para criar state.md inicial
python orchestrator.py

# Verificar que state.md foi criado
cat state.md

# Você verá:
# - 13 tasks mapeadas
# - Week 1 com 4 tasks
# - Todas marcadas como [ ] (não iniciadas)
```

### Passo 2: Executar DevOps Agent Manualmente

```python
# Abrir Python REPL
python

>>> from orchestrator import StateManager, DevOpsAgent
>>> state = StateManager()
>>> devops = DevOpsAgent(state)
>>> devops.run()

# Agent vai:
# 1. Pegar primeira task disponível (Docker setup)
# 2. Marcar como [⏳] in progress
# 3. Executar task (neste caso, você implementa ou ele simula)
# 4. Marcar como [] completo
# 5. Atualizar state.md
```

**Nota:** Na Opção 1 (manual), você mesmo implementa cada task ou os agents apenas simulam. É útil para entender o fluxo, mas não gera código real.

### Passo 3: Monitorar State

```bash
# Em outro terminal, monitore state.md
watch -n 2 cat state.md

# Você verá atualizações em tempo real:
# [⏳] DevOps: Docker setup - iniciado 16:00
# [] DevOps: Docker setup completo 16:30
# [⏳] Backend: Database schema - iniciado 16:35
```

### Passo 4: Completar Week 1

```bash
# Continue executando agents manualmente ou deixe o loop:
python orchestrator.py

# Ele vai executar sequencialmente:
# 1. DevOps Agent → Docker
# 2. Backend Agent → DB Schema  
# 3. Backend Agent → Copy Engine
# 4. Test Agent → Validation

# Ao final, state.md mostrará:
# Week 1: 100% 
```

---

##  Parte 3: Execução Automatizada (Opção 2) - 2 horas

Esta é a opção RECOMENDADA onde Claude Code realmente implementa o código.

### Passo 1: Instalar Claude Code

```bash
# Seguir instruções em https://claude.ai/code
# Após instalado, validar:
claude code --version
```

### Passo 2: Configurar Claude Code Agent

```bash
# O arquivo claude_code_agents.py já está pronto
# Validar que funciona:
python -c "from claude_code_agents import AutomatedDevOpsAgent; print('OK')"
```

### Passo 3: Executar Week 1 Automatizada

```bash
# Inicia build automatizado de Week 1
python claude_code_agents.py --week 1

# O que vai acontecer:
# 
# [16:00] Orchestrator lê CLAUDE.md e cria tasks
# 
# [16:05] DevOps Agent chamando Claude Code...
#         Claude Code cria docker-compose.yml
#         Claude Code cria .env.example
#         Claude Code testa com docker-compose up
#          Docker setup completo
#         state.md atualizado
#
# [16:35] Backend Agent chamando Claude Code...
#         Claude Code cria app/models/transfer.py
#         Claude Code configura SQLAlchemy
#         Claude Code roda alembic migrations
#          Database schema completo
#         state.md atualizado
#
# [17:05] Backend Agent chamando Claude Code...
#         Claude Code implementa copy_engine.py
#         Claude Code cria testes
#          Copy Engine completo
#         state.md atualizado
#
# [17:40] Test Agent chamando Claude Code...
#         Claude Code cria test_copy_1file.py
#         Claude Code executa pytest
#          Testes passando
#         state.md atualizado
#
# [17:50]  WEEK 1 COMPLETA!
```

### Passo 4: Monitorar Execução

```bash
# Terminal 1: Execução
python claude_code_agents.py --week 1

# Terminal 2: Monitorar state.md
watch -n 5 cat state.md

# Terminal 3: Monitorar logs
tail -f logs/multiagent.log

# Terminal 4: Ver código sendo gerado
watch -n 10 'find app/ -type f -name "*.py" -exec echo {} \; -exec wc -l {} \;'
```

### Passo 5: Validar Resultado

```bash
# Após Week 1 completar, validar:

# 1. Docker está rodando?
docker-compose ps
# Deve mostrar: postgres, redis, api, worker (todos healthy)

# 2. Database foi criado?
docker-compose exec postgres psql -U ketter -c "\dt"
# Deve mostrar: transfers, checksums, audit_logs

# 3. Copy Engine funciona?
python -c "from app.services.copy_engine import copy_with_verification; print('OK')"

# 4. Testes passam?
pytest tests/test_copy_engine.py -v
# Deve mostrar: 5/5 tests passing

# 5. State.md está atualizado?
grep "Week 1" state.md
# Deve mostrar: Week 1: 100% 
```

---

##  Parte 4: Build Completo (4-6 horas)

### Passo 1: Executar Build Completo

```bash
# Isso vai executar todas as 4 semanas automaticamente
python claude_code_agents.py --full

# O sistema vai:
# - Week 1: Docker + DB + Copy Engine (1-2h)
# - Week 2: API + Worker + Integration (1-2h)
# - Week 3: Frontend React (1h)
# - Week 4: PDF Reports + Tests + Docs (1h)
#
# Total: 4-6 horas
```

### Passo 2: Acompanhar Progresso

```bash
# Dashboard de progresso
watch -n 10 'echo "=== KETTER 3.0 BUILD ===" && \
             grep "Status Geral" state.md && \
             echo "" && \
             grep "Week [1-4]:" state.md'

# Você verá algo como:
# === KETTER 3.0 BUILD ===
# Status Geral: 8/13 tasks (62%)
# Week 1: 100% 
# Week 2: 100% 
# Week 3: 50% ⏳
# Week 4: 0%
```

### Passo 3: Lidar com Falhas (se houver)

```bash
# Se um agent falhar, state.md mostrará:
# [] Backend: Copy Engine - BLOCKED
#     Error: ImportError: ...

# Opções:

# 1. Retry automático
python claude_code_agents.py --retry backend_copy_engine

# 2. Fix manual e continue
# - Corrija o código
# - Atualize state.md: [] → []
# - Continue: python claude_code_agents.py --continue

# 3. Skip e voltar depois
python claude_code_agents.py --skip backend_copy_engine
```

### Passo 4: Validação Final

```bash
# Quando build completo, executar validação final:

# 1. Todos testes passam?
pytest tests/ -v --cov=app
# Target: 100% coverage nos módulos core

# 2. Docker funciona sem workarounds?
docker-compose down && docker-compose up -d
docker-compose ps
# Todos healthy?

# 3. Frontend funciona?
curl http://localhost:3000
# Status 200?

# 4. API funciona?
curl http://localhost:8000/docs
# Swagger UI carrega?

# 5. Teste real de 500GB (Week 4 task)
# Este precisa de storage adequado
python tests/test_500gb.py
# Deve copiar 500GB com zero erros e checksums OK
```

---

##  Parte 5: Debugging e Troubleshooting

### Problema 1: Agent Trava

```bash
# Sintoma: Agent não progride, stuck em [⏳]

# Solução:
# 1. Ver logs
tail -50 logs/backend_agent.log

# 2. Identificar onde travou
# Ex: Esperando Claude Code que não responde

# 3. Kill e restart
# Ctrl+C no terminal
python claude_code_agents.py --resume

# state.md mantém estado, então recomeça de onde parou
```

### Problema 2: Claude Code Falha

```bash
# Sintoma: Error: Claude Code timeout ou erro

# Solução:
# 1. Verificar Claude Code funciona
claude code "Hello world"

# 2. Simplificar prompt
# Editar claude_code_agents.py
# Reduzir complexidade do prompt

# 3. Aumentar timeout
# No claude_code_agents.py, linha ~50:
timeout=1200  # 20 minutos em vez de 10
```

### Problema 3: Dependências Não Desbloqueiam

```bash
# Sintoma: Task deveria desbloquear mas continua [ ]

# Solução:
# 1. Verificar state.md
cat state.md | grep "BLOQUEADO"

# 2. Checar dependências
python -c "
from orchestrator import StateManager
state = StateManager()
task = state.get_task('backend_copy_engine')
print(f'Deps: {task.dependencies}')
for dep in task.dependencies:
    dep_task = state.get_task(dep)
    print(f'{dep}: {dep_task.status}')
"

# 3. Forçar desbloqueio se for bug
# Editar state.md manualmente:
# [] → [] na dependência
```

### Problema 4: State.md Corrompido

```bash
# Sintoma: Errors ao ler state.md

# Solução:
# 1. Backup existe?
ls -la state.md.backup

# 2. Recriar do state.json
python -c "
from orchestrator import StateManager
state = StateManager()
state.load()  # Carrega do JSON
state.save()  # Regenera MD
"

# 3. Pior caso: Reiniciar
mv state.md state.md.broken
python orchestrator.py  # Cria novo
# Marque manualmente as tasks já completas
```

---

##  Parte 6: Métricas e Monitoramento

### Dashboard em Tempo Real

```bash
# Crie um script de dashboard
cat > dashboard.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo ""
    echo "   KETTER 3.0 MULTI-AGENT BUILD STATUS     "
    echo ""
    echo ""
    
    # Progresso geral
    grep "Status Geral" state.md
    echo ""
    
    # Por week
    grep -A 1 "Week [1-4]:" state.md | head -8
    echo ""
    
    # Próximas ações
    echo ""
    echo "   PRÓXIMAS AÇÕES                          "
    echo ""
    grep -A 5 "Próximas Ações" state.md | tail -5
    echo ""
    
    # Última atualização
    grep "Última Atualização" state.md
    
    sleep 5
done
EOF

chmod +x dashboard.sh
./dashboard.sh
```

### Métricas Customizadas

```python
# metrics.py
from orchestrator import StateManager

def show_metrics():
    state = StateManager()
    
    # Progresso
    progress = state.get_progress()
    print(f"Progress: {progress['percentage']:.1f}%")
    print(f"Completed: {progress['completed']}/{progress['total']}")
    
    # Por agente
    agents = {}
    for task in state.tasks.values():
        if task.agent not in agents:
            agents[task.agent] = {'total': 0, 'done': 0}
        agents[task.agent]['total'] += 1
        if task.status.value == '':
            agents[task.agent]['done'] += 1
    
    print("\nBy Agent:")
    for agent, stats in agents.items():
        pct = stats['done'] / stats['total'] * 100
        print(f"  {agent}: {pct:.0f}% ({stats['done']}/{stats['total']})")

if __name__ == "__main__":
    show_metrics()
```

---

##  Parte 7: Checklist de Sucesso

### Week 1 Checklist

```
[ ] Docker Compose criado e funcional
[ ] PostgreSQL acessível em :5432
[ ] Redis acessível em :6379
[ ] Database schema criado (3 tabelas)
[ ] Migrations funcionam (alembic upgrade head)
[ ] Copy Engine implementado
[ ] SHA-256 triplo funciona
[ ] Validação de espaço em disco funciona
[ ] Testes unitários: 100% coverage
[ ] Teste de 1GB: passa
[ ] state.md: Week 1 = 100%
```

### Week 2 Checklist

```
[ ] API endpoints criados
[ ] RQ Worker configurado
[ ] Jobs podem ser enqueueados
[ ] Progress updates via Redis
[ ] Retry policy funciona
[ ] API + Worker integração OK
[ ] Testes de integração passam
[ ] state.md: Week 2 = 100%
```

### Week 3 Checklist

```
[ ] React app funcional
[ ] File picker funciona
[ ] Progress bar atualiza
[ ] History mostra transfers
[ ] Frontend ↔ API integração OK
[ ] state.md: Week 3 = 100%
```

### Week 4 Checklist

```
[ ] PDF reports gerados
[ ] Testes end-to-end passam
[ ] Teste 500GB: sucesso
[ ] Documentação completa
[ ] Docker robusto (zero workarounds)
[ ] MRC principles validados
[ ] state.md: Week 4 = 100%
[ ]  PRODUCTION READY
```

---

##  Conclusão

Você agora tem:

 Sistema multi-agente completo  
 Instruções passo-a-passo  
 Debugging guides  
 Métricas e monitoramento  
 Checklists de validação  

**Próximos Passos:**

1. Escolha sua opção (Manual ou Automatizada)
2. Siga o tutorial correspondente
3. Monitore via state.md
4. Valide cada week antes de avançar
5. Em 4-6 horas, terá Ketter 3.0 pronto!

**Boa sorte! **

---

*Tutorial v1.0 - Sistema Multi-Agente Ketter 3.0*
