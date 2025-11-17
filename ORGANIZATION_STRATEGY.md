# Ketter — Organization Strategy
Versão 1.0  
Escopo: Reorganização completa do repositório para arquitetura profissional e escalável.

---

## 1. Propósito
Descrever a estrutura final de diretórios e módulos do Ketter após a reorganização completa, garantindo:

- modularidade clara  
- separation of concerns  
- compatibilidade total com Codex CLI  
- suporte nativo ao Hardening TPN/MPA  
- organização profissional nível estúdio  

---

## 2. Estrutura Final Desejada

ketter/
app/
core/ # engine, watcher, transfer logic
security/ # path sanitizer, whitelist, hashing, chain-of-custody
services/ # jobs, background tasks, async engine
routers/ # API endpoints (futuro)
schemas/ # Pydantic schemas
models/ # ORM models
utils/ # helpers isolados
config/ # configs e loaders de YAML/JSON
tests/
unit/
integration/
regression/
hardening/
scripts/
ketter-dev.sh
ketter-harden.sh
resources/
samples/
docs/
strategy.md
HARDENING_TPN_MPA_STRATEGY.md
blueprint.md
blueprint-hardening.md
blueprint-organization.md
state.md
state-hardening.md
state-organization.md
STRATEGY_PROMPT.md
README.md
pyproject.toml / requirements.txt

yaml
Copy code

---

## 3. Regras de Reorganização

### 3.1 Sem apagar código
Nenhum arquivo funcional pode ser removido ou sobrescrito.

### 3.2 Atomicidade
Cada movimento de arquivo deve ser testado por:

PYTHONPATH=. pytest

yaml
Copy code

### 3.3 Rollback Total
Se qualquer import quebrar → rollback → registrar falha → parar ciclo.

### 3.4 Atualização de Imports
Todos os `from x import y` devem ser corrigidos automaticamente.

### 3.5 Testes
Todos os testes existentes devem passar após a reorganização.

### 3.6 Documentação Sincronizada
Após a conclusão, atualizar README.md e docs com a nova estrutura.

---

## 4. Compatibilidade com Hardening TPN/MPA

A reorganização prepara:

- `core/` para mover lógica do engine  
- `security/` para receber o Hardening Layer  
- `services/` para processamento assíncrono e multi-hop  
- `tests/hardening/` para suite de compliance  
- logs forenses estruturados  
- path sanitization avançada  

---

## 5. Execução via Codex

O ciclo será sempre:

1. Read STRATEGY_PROMPT.md  
2. Read ORGANIZATION_STRATEGY.md  
3. Read blueprint-organization.md  
4. Ler state-organization.md  
5. Executar tarefa atômica  
6. Testar  
7. Commit ou rollback  
8. Atualizar state-organization.md 
