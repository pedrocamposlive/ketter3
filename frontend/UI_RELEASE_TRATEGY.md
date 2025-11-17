1. Objetivo da Fase

Concluir a integração da UI Manus dentro do Ketter 3.0, garantindo:

Layout corporativo padronizado (tokens, grid, spacing)

Dashboard completo e responsivo

Todas as páginas alinhadas ao design Manus

Build final validado

Documentação e preparação para release

A fase termina quando:

state-ui-manus.md estiver 100% completo

O build produzir dist/ estável

A UI operar integralmente com o backend real

2. Entradas

docs/state-ui-manus.md

docs/ui-manus-blueprint.md

Código React em /frontend

Tokens e theme system

Layout base + componentes funcionais

3. Escopo da Fase
3.1. Finalizar Manus Tokens

 Revisar paleta

 Revisar spacing / radius / shadows / transitions

 Revisar breakpoints

 Validar tokens em todas as páginas

3.2. Global Layout

 .ui-container final

 Responsividade Manus

 Aplicação global de spacing

 Refinamento de páginas secundárias

3.3. Páginas Individuais

 Dashboard (KPI, charts, alerts)

 Transfers (cards, grids, details)

 Audit (timeline, logs)

 Health (metrics grid)

 Settings (fieldset enterprise)

3.4. Polish Final

 Normalizar radius, sombras, spacing

 Remover classes mortas

 Consolidar App.css

 Revisar tipografia

 Conferir hierarquia unificada

4. Build & Release
4.1. Build

Operador deve rodar:

cd frontend
npm install
npm run build


Objetivo: validar dist/ para produção.

4.2. Fixes pós-build

Ajustar imports

Resolver APIs faltantes

Ajustar proxies

Revisar environment variables

4.3. Smoke Test

Executar:

./scripts/smoke-ui.sh


Validar:

Dashboard carrega

Transfers sincroniza

Audit logs atualizam

Health OK

Settings salva/mostra

5. Documentação

Criar/atualizar:

docs/state-ui-manus.md (100% tasks)

docs/final-polish.md

docs/UI-RELEASE-NOTES.md

Atualizar README com seção “UI Manus Revamp”

6. Critérios de Conclusão

A fase termina quando:

Todas tasks do state-ui-manus.md estiverem [x]

Build final bem-sucedido

Smoke Test aprovado

UI responsiva em 4 breakpoints

Layout unificado e estável

Nenhum componente legado (pré-Manus) ativo

7. Próximas Fases

Após completar a UI Manus Integration:

Criar Ketter Operator Guide

Criar Security Guide (TPN/MPA)

Criar Deploy Guide (Docker/Nginx/systemd)

Criar Test Guide (fluxos de transferência)

Criar API Reference automatizada
