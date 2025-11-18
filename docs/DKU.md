KETTER 3.0 — DKU (Discreet Kernel Utility) Modernizado

Objetivo

Estabelecer um processo padronizado e reproducível de instalação, validação e diagnóstico do ambiente Ketter 3.0 em um macOS limpo (Apple Silicon), inspirado no conceito histórico do DKU da Discreet/Autodesk. Este documento descreve toda a arquitetura do DKU, sua lógica de execução, seus módulos e como será utilizado pelo Codex CLI como agente executor.

Visão Geral do DKU

O DKU é um conjunto de módulos que garante:

Instalação consistente e controlada.

Verificação de hardware e ambiente.

Validação completa de serviços essenciais.

Configuração automática dos componentes do Ketter.

Relatórios estruturados, detalhados e versionados.

Todo o fluxo é automatizado, sem intervenção manual.
O Codex CLI será responsável por executar cada etapa, capturar resultados e gerar relatórios.

Estrutura de Diretórios

dku/
   00_hardware_check.sh
   01_system_prep.sh
   02_install_dependencies.sh
   03_install_ketter_services.sh
   04_post_install_validation.sh
   05_generate_report.sh

dku_run.sh

Os relatórios gerados ficarão em:

docs/dku_reports/
   report_YYYYMMDD_HHMM.md

Fluxo Completo do DKU

1. Verificação de Hardware (00_hardware_check.sh)

Valida:

Modelo do Mac

Arquitetura ARM64

Memória total

Espaço em disco

Estado do sistema

Disponibilidade de portas essenciais

2. Preparação do Sistema (01_system_prep.sh)

Executa ajustes iniciais:

Instala Homebrew (se necessário)

Garante permissões de diretórios

Prepara estrutura de logs e relatórios

Verifica ferramentas essenciais

3. Instalação de Dependências (02_install_dependencies.sh)

Instala:

Python 3.11

PostgreSQL 16

Redis

Node.js 20

Ferramentas CLI necessárias

Configura serviços

4. Instalação dos Serviços do Ketter (03_install_ketter_services.sh)

Cria virtualenv

Instala requirements Python

Instala frontend

Gera .env automaticamente

Aplica migrações Alembic

Configura LaunchAgents (backend e worker)

5. Validação Pós-Instalação (04_post_install_validation.sh)

Testa PostgreSQL (pg_isready)

Testa Redis

Testa backend (uvicorn)

Testa RQ Worker

Testa frontend Vite

Executa testes unitários e end-to-end

Registra todos os resultados

6. Geração de Relatório (05_generate_report.sh)

Gera um relatório consolidado contendo:

Logs completos

Resultados de cada etapa

Falhas e análises

Recomendações

Resumo técnico do ambiente

Orquestrador Principal: dku_run.sh

Este script controla todo o fluxo:

Executa cada módulo em sequência.

Para automaticamente se ocorrer falha crítica.

Gera logs intermediários.

Chama o módulo final de relatório.

Integração com o Codex CLI

O Codex CLI atuará como o executor oficial do DKU.

Funções do Codex:

Executar cada módulo do DKU.

Capturar stdout e stderr.

Verificar falhas.

Produzir relatórios em Markdown.

Auditar mudanças.

Rodar novamente cada etapa on-demand.

Exemplo de prompt para o Codex:

Task: Execute the full DKU workflow.
Run dku_run.sh and capture all logs.
If any module fails, stop execution and generate docs/dku_reports/report_<timestamp>.md with:
- full output
- analysis
- pass/fail summary
- recommended fixes

Benefícios Esperados

Ambiente padronizado para todos os desenvolvedores

Redução de erros de instalação

Relatórios claros e rastreáveis

Processo inspirado nos melhores padrões Autodesk/Discreet

Base sólida para expansão em Linux e Windows

Próximos Passos

Gerar o arquivo dku_run.sh no canvas.

Gerar cada módulo da pasta dku/.

Integrar no fluxo Codex CLI.

Validar DKU em um macOS limpo M1.

Este DKU.md servirá como referência principal para a implementação completa do sistema DKU do Ketter 3.0.
