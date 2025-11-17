# Blueprint — Organization Phase  
Versão 1.0  
Fluxo operacional para reorganização completa do Ketter

---

## 1. Ciclo Codex

Cada tarefa segue:

1. Read phase  
2. Locate task  
3. Implement atomic change  
4. Test  
5. Rollback on failure  
6. Commit on success  
7. Update state  
8. Stop or continue  

---

## 2. Read Phase

O assistente deve sempre iniciar com:

- Read STRATEGY_PROMPT.md  
- Read ORGANIZATION_STRATEGY.md  
- Read blueprint-organization.md  

---

## 3. Locate Task

Abrir:

docs/state-organization.md

yaml
Copy code

Selecionar o próximo `[ ]` (unchecked).

---

## 4. Implementação

Regras:

- Usar caminhos relativos  
- Atualizar imports  
- Não mover arquivos parcialmente  
- Evitar sobrescritas  
- Criar diretórios faltantes  
- Manter histórico Git limpo  
- Evitar renomeações desnecessárias  

---

## 5. Testes

Executar após cada mudança:

PYTHONPATH=. pytest

nginx
Copy code

Se existirem regressões específicas:

pytest tests/unit
pytest tests/integration
pytest tests/regression

yaml
Copy code

---

## 6. Rollback

Se qualquer teste falhar:

- reverter o patch aplicado  
- atualizar state com o erro  
- parar o ciclo  

---

## 7. Commit

Se todos os testes passarem:

- criar commit  
- atualizar state-organization.md com timestamp  
- prosseguir para o próximo item  

---

## 8. Finalização

Quando `state-organization.md` estiver totalmente marcado:

- atualizar README.md  
- atualizar docs/  
- gerar architecture.png  
- registrar conclusão da fase
