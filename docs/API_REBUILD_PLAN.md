# API_REBUILD_PLAN.md  
Fase: API Reconstruction (Final)

Objetivo:
Gerar um arquivo `frontend/src/services/api.js` completo, alinhado 1:1 com:
- Todos os endpoints existentes do backend FastAPI
- Todos os imports feitos nos componentes React
- Todos os endpoints necessários para o Dashboard, Transfers, Audit, Health, Settings

Processo que o Codex deve seguir:

## ETAPA 1 — Ler as fontes de verdade
- app/main.py
- app/routers/**
- app/schemas/**
- app/models/**
- frontend/src/**/*

## ETAPA 2 — Construir o mapa de importações
Para cada arquivo React:
- Extrair nomes importados de `../services/api`
- Mapear todas as funções chamadas no código (mesmo se não importadas)
- Gerar lista completa de funções necessárias

## ETAPA 3 — Cruzar com o backend
Para cada função:
- Identificar endpoint equivalente no backend
- Inferir:
  - método (GET/POST/DELETE)
  - rota
  - payload
  - parâmetros
  - modelo de retorno

## ETAPA 4 — Gerar api.js definitivo
Reescrever completamente o arquivo com:
- secureFetch (padrão do Ketter)
- Todas as funções exportadas
- Erros tratados (ApiError)
- Compatibilidade total com React
- Alinhamento aos componentes existentes
- Sem placeholders
- Sem funções faltando
- Sem funções extras
- Sem divergências

## ETAPA 5 — Patch automático
Codex deve:
- Reescrever api.js
- Ajustar nomes quebrados nos componentes se necessário
- Rodar "git add" e "git commit"

## ETAPA 6 — Build Test (ação humana)
Operador deve rodar:

    cd frontend
    npm install
    npm run build

## ETAPA 7 — Validação
Se build passar:
- Adicionar PATCH API_REBUILD_COMPLETE em docs/state-ui-manus.md
- Confirmar finalização do frontend.

Se build falhar:
- Codex deve rodar novamente o ciclo, ajustando diferenças até build passar.

Fim do plano.

