UI Blueprint — Hybrid Workflow (Manus → Codex → Local Build)

Versão: 1.0

1. Objetivo

Estabelecer um blueprint operacional onde:

O Codex gera todo o código da UI.

O usuário executa npm install / npm run dev / npm run build localmente.

O fluxo continua atômico, consistente com o backend.

2. Princípios

Codex nunca roda npm no sandbox.

Codex gera, organiza, refatora e mantém tudo dentro de frontend/.

Usuário garante a parte local: build, preview e testes manuais.

Tudo registrado em docs/state-ui.md.

3. Ciclo Operacional
Passo 1 — Leitura

Codex lê:

STRATEGY_PROMPT.md

docs/STRATEGY_UI.md

docs/ui-blueprint.md

docs/state-ui.md

Passo 2 — Identificação

Codex identifica o próximo item [ ] em docs/state-ui.md.

Passo 3 — Execução Codex

Para cada task:

Criar / editar arquivos do frontend

Criar componentes

Criar páginas

Criar rotas

Criar design tokens e theme

Estruturar pastas conforme blueprint

Refatorar código existente

Garantir consistência de imports

Nunca executar npm.

Passo 4 — Execução HUMANA

Sempre que a task envolver:

npm install

npm run dev

npm run build

O blueprint marca estas etapas como:

"AÇÃO HUMANA NECESSÁRIA — validar build local antes de continuar"

Passo 5 — Finalização

Codex atualiza docs/state-ui.md

Codex commita as mudanças

Retorna ao início do ciclo

4. Diretórios da UI
frontend/
  package.json
  vite.config.js
  index.html
  src/
    app/
    components/
    features/
    pages/
    hooks/
    lib/
    styles/
    ui/ (shadcn)
5. Tarefas típicas (que o Codex fará)

Criar página Dashboard

Criar layout base

Criar Sidebar

Criar Header

Criar sistema de temas

Integrar API do Ketter

Criar componentes: Cards, Tables, Logs Viewer

Criar estados de Loading, Empty, Error

Criar workflow de Transfer Details

Criar página de Health, Metrics

6. Itens que dependem de AÇÃO HUMANA

Instalar dependências (npm install)

Rodar build (npm run build)

Testar visualmente (npm run dev)

7. Validação

Estado visual coerente com wireframes Manus

Componentes funcionando

Build local sem erros
