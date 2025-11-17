# Ketter 3.0 – UI Blueprint
Versão: 1.0
Documento Operacional (Executável pelo Codex)

Objetivo

Este blueprint define exatamente como a UI será implementada, incluindo estrutura de pastas, arquivos, nomenclatura, regras de integração, testes e ciclos de execução. Ele é obrigatório para execução automatizada via Codex.


Estrutura de Diretórios

ketter/
  app/
  frontend/
    src/
      components/
      pages/
      layout/
      hooks/
      services/
      assets/
      theme/
    public/
    package.json


Ciclo de Execução Codex

1. Ler STRATEGY_UI.md
2. Ler ui-blueprint.md
3. Abrir state-ui.md
4. Obter a primeira tarefa [ ]
5. Executar atomicamente
6. Rodar:
   npm install
   npm run build (ou equivalente)
7. Se build falhar:
   rollback completo
8. Se build passar:
   commit profissional
   marcar tarefa concluída no state-ui.md


Regras de Criação de Componentes

1. Todos componentes devem ser funcionais
2. Devem usar hooks
3. Código deve ser dividido por responsabilidade
4. Nada de inline styles
5. Todo tema deve ficar em theme/
6. Importações absolutas: @components, @pages, etc.


Páginas Principais

1. Dashboard
   - Status geral
   - Indicadores de jobs
   - Throughput

2. Transfers
   - Criar job
   - Exibir progresso em tempo real
   - Logs

3. Audit
   - Auditoria
   - Histórico
   - Busca

4. System Health
   - Estado do backend
   - Latência
   - Filas RQ

5. Settings
   - Volumes permitidos
   - Perfis
   - Configurações gerais


Regras de Integração com Backend

1. Todas requisições usam services/api.js
2. Erros devem ser tratados com try/catch
3. Backend não pode ser modificado sem patch aprovado
4. A UI deve respeitar retornos do backend sem mascarar erros


Testes Obrigatórios

1. Teste de build
2. Teste de rotas
3. Teste de imports
4. Teste de assets
5. Teste de API mocking opcional


Padronização de Commits Codex

feat(ui): descrição técnica
fix(ui): correção técnica
chore(ui): ajustes menores
refactor(ui): melhorias internas


Rollback

Se qualquer parte falhar:
1. Restaurar arquivo anterior
2. Desfazer commit local
3. Reverter alterações pendentes


Fechamento

A UI só é considerada finalizada quando:
1. Todas tarefas do state-ui.md estiverem marcadas
2. O build final passar
3. A arquitetura estiver íntegra
