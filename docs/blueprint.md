Ketter / Sefirot — Blueprint Operacional de Execução Assistida

Versão 1.0 — Completo (opção C)
Documento oficial para orquestrar sprints e ciclos do projeto.

1. Propósito do Blueprint

Este documento define como o assistente (Codex CLI ou ChatGPT) deve:

ler a documentação mestre

selecionar tarefas

executar implementações

testar

commitar

aplicar rollback se necessário

atualizar state.md

evoluir o sistema até 100% operacional

O blueprint é a linha de produção oficial do projeto.

2. Ordem Obrigatória de Leitura

Sempre que iniciar qualquer execução, o assistente deve:

Ler STRATEGY_PROMPT.md

Ler strategy.md

Ler README.md

Ler blueprint.md (este arquivo)

Ler state.md

Ler enhance.md

Nenhuma ação deve ocorrer sem seguir essa ordem.

3. Ciclo Fundamental (Loop de Execução)

O sistema sempre segue este loop:

Identificar a próxima tarefa ativa em state.md

Validar prioridade e dependências

Planejar a implementação

Escrever código mínimo necessário

Executar testes funcionais e de falha

Aplicar rollback em caso de erro

Validar integridade operacional

Criar commit padronizado

Atualizar state.md

Avançar para a próxima tarefa

Este loop nunca deve ser quebrado.

4. Tipos de Sprints

O projeto possui quatro tipos de sprints:

4.1. Sprint de Implementação

Criar ou modificar funcionalidade do Ketter:

watcher

COPY/MOVE

zip/unzip

validação

logs

auditoria

config

API

UI

4.2. Sprint de Correção (Fix)

Corrige bugs, inconsistências ou comportamentos inesperados.

4.3. Sprint de Documentação

Atualiza:

state.md

README

enhance.md

strategy.md

arquivos de configuração

4.4. Sprint de Infraestrutura

Alterações estruturais:

ACL

Samba montagens

systemd

paths

configuração YAML

logs

5. Critérios de Aceitação (Definition of Done)

Uma tarefa só é considerada concluída quando:

O código funciona.

O teste passou (funcional + falha).

O rollback funciona.

A documentação foi atualizada.

O commit foi realizado.

state.md foi marcado como concluído.

Nenhuma regressão foi introduzida.

Logs foram validados.

Se algum item falhar → não está concluído.

6. Testes Obrigatórios

Cada sprint deve incluir os seguintes testes:

6.1. Testes de Sucesso

COPY

MOVE

pasta com muitos arquivos (zip)

validação de hash

watcher detectando eventos

paths válidos

zip/unzip

6.2. Testes de Falha

path inexistente

permissão negada

zip corrompido

falha de disco

perda de conexão

MOVE interrompido

unzip parcial

hash mismatch

6.3. Testes de Performance

Somente quando aplicável:

zip de 2000+ arquivos

COPY de arquivos grandes

watchers intensos

7. Regras de Rollback

Rollback deve sempre ser:

seguro

atômico

reversível

com logs

previsível

documentado

MOVE

nunca apagar origem antes da validação

se falhar: deletar destino parcial e preservar origem

ZIP

falha no unzip: preservar ZIP e remover pasta parcial

Watcher

evitar deadlocks

desbloquear fila

8. Padronização de Commits

Formato obrigatório:

feat: ...
fix: ...
refactor: ...
docs: ...
perf: ...
test: ...
build: ...


Commits devem ser:

isolados

pequenos

atômicos

rastreáveis

9. Como Selecionar Tarefas

O assistente deve:

Abrir state.md

Identificar o bloco Prioridade P1

Selecionar a primeira tarefa não concluída

Validar com strategy.md

Executar o ciclo completo

Quando P1 acabar → seguir para P2.

10. Integração com enhance.md

Sempre que uma oportunidade de melhoria surgir:

registrar em enhance.md

nunca implementar diretamente

aguardar promoção para state.md

11. Estrutura do Sprint

Cada sprint deve ser executado assim:

11.1. Preparação

ler strategy.md

analisar state.md

coletar dependências

criar plano

11.2. Execução

escrever código

manter modularidade

seguir padrões

11.3. Testes

sucesso

falha

performance (se aplicável)

11.4. Rollback (se falhar)

Restaurar estado seguro.

11.5. Commit

Registrar mudança.

11.6. Documentação

Atualizar:

state.md

enhance.md (se necessário)

12. Regras para Assistentes (Codex CLI)

O assistente:

deve sempre seguir strategy.md

nunca inventar funcionalidades

nunca alterar o blueprint sem autorização

sempre validar paths

sempre criar logs

sempre testar

sempre commitar atomicamente

sempre atualizar state.md

13. Política de Segurança

Obrigatório:

SHA-256

logs JSON

paths autorizados

sem SMB cross-VLAN

sem operações destrutivas antes de validação

rollback seguro

14. Fases Oficiais do Desenvolvimento
14.1. Fase 1 — Estabilização

Watcher, COPY/MOVE, logs, zip/unzip, paths seguros

14.2. Fase 2 — Observabilidade

Prometheus + Grafana

14.3. Fase 3 — API

Monitoramento remoto

14.4. Fase 4 — RBAC

LDAP/AD

14.5. Fase 5 — UI

PySide6 + Web

14.6. Fase 6 — Extensões

Plugins do pipeline
