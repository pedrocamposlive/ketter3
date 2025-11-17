KETTER — HARDENING BLUEPRINT
Versão 1.0 — Execução Atômica, Determinística e Segura
1. Objetivo do Blueprint

Este blueprint descreve como o Codex CLI deve executar cada tarefa listada em docs/state-hardening.md, garantindo:

atomicidade

testes completos

rollback seguro

commits mínimos e limpos

comportamento determinístico

execução compatível com TPN/MPA

isolamento inter-VLAN

segurança e consistência

Cada tarefa deve resultar em:

Patch aplicado

Testes executados

Commit realizado

state-hardening atualizado

Encerramento do ciclo

Sem exceções.

2. Ciclo Geral

O Codex deve, em cada execução:

Ler STRATEGY_PROMPT.md

Ler docs/strategy-hardening.md

Ler docs/blueprint-hardening.md

Abrir docs/state-hardening.md

Identificar o primeiro item não marcado com [ ]

Executar o ciclo descrito abaixo

Rodar testes

Commitar

Atualizar o state

Encerrar o ciclo sem comentários adicionais

3. Estrutura do Ciclo Atômico

Cada tarefa do hardening deve seguir exatamente esta ordem:

3.1. Preparação

Carregar o contexto dos documentos

Verificar dependências da tarefa

Avaliar riscos e impacto

Criar patch em memória

3.2. Aplicação do Patch

O patch deve:

ser mínimo

manter padrões do projeto

não gerar dívida técnica

preservar compatibilidade com testes

respeitar os princípios de segurança

3.3. Testes

Executar sempre:

DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest


E validar:

100% verde

nenhum erro

warnings apenas os já existentes

3.4. Commit

Commit message deve seguir:

hardening: <descrição curta da ação>
<detalhes técnicos adicionais>

3.5. Atualização do state-hardening.md

Marcar com [x]

Incluir timestamp UTC

Descrever evidências de testes

Finalizar task

3.6. Encerrar o ciclo

Sempre parar após concluir uma tarefa.

4. Categorias de Tarefas do Hardening

Cada bloco abaixo corresponde a seções do state-hardening.md que o Codex executará.

4.1. Filesystem Hardening
Tarefas previstas

Sanitização avançada de path

Unicode fold normalizado

Regex de caracteres proibidos

Verificação de volume com whitelist expandida

Normalização de permissões

Bloqueio absoluto de symlinks

Proteção a directory traversal

Randomização segura de tmpdirs

Criptografia e hashing opcional para logs críticos

Blueprint de Execução

Para cada tarefa:

Criar patch em app/security/

Atualizar imports se necessário

Garantir integração com:

watcher

engine

zip handler

transfer flow

Criar testes específicos em:

tests/security/

tests/integration/

Validar snapshots de logs

Commit + Atualizar state

4.2. ZIP Secure Hardening
Tarefas previstas

ZIP store-only reforçado

Máximo tamanho por arquivo

Bloqueio de paths maliciosos no ZIP

Scrubbing de metadata

Validação pós-extração

CRC32 e SHA-256 comparativos

Blueprint

Atualizar app/services/zip_handler.py

Criar testes → tests/services/test_zip_hardening.py

Validar extração determinística

Commit + update state

4.3. MOVE/COPY Hardening
Tarefas previstas

Idempotência total

Rollback aprimorado

Verificação HASH-before-after

Execução atomic via temp-file rename

Detecção de partial writes

Circuit-breaker de destino

Proteção contra overwrite inseguro

Blueprint

Atualizar engine MOVE/COPY

Criação de testes críticos

Simulação de falhas (fault injection)

Commit

Update state

4.4. Watcher Hardening
Tarefas previstas

Novo loop resistente a falhas

Timeout configurável

Break detection

Filtro de arquivos invisíveis reforçado

Modo inter-VLAN

Supervisão de threads

Blueprint

Mexer somente em app/services/watcher.py

Criar testes → tests/integration/test_watcher_hardening.py

Validar detecção massiva

Commit + update state

4.5. ACL / Permissão Hardening
Tarefas previstas

ACL POSIX

Samba create mask enforcement

Permissões SUID/SGID

Minimização de privilegios

Execução segura em VLANs

Blueprint

Criar módulo ACL: app/security/acl.py

Criar testes de permissão:

tests/security/test_acl.py

Commit + update state

4.6. Network / VLAN Hardening
Tarefas previstas

Transfer Node isolation

VLAN binding

Proibição de cross-VLAN SMB

Execução assíncrona

Blueprint

Criar módulo app/core/vlan_router.py

Criar testes relacionados

Commit + update state

4.7. Forensics & Audit Hardening
Tarefas previstas

Log imutável

Timestamps UTC strict

Log hashing

ID de fluxo

Auditoria diária

Auditoria mensal

Auditoria semestral

Blueprint

Criar módulo app/security/forensics.py

Criar testes forenses

Atualizar watchers/engines

Commit + update state

5. Testes Obrigatórios

Todos os ciclos devem executar a suíte completa:

DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest


Com:

100% testes passando

sem regressões

sem warnings inesperados

6. Critérios Final de Aceitação

A fase de hardening será considerada concluída quando:

Todos os itens do state-hardening.md estiverem [x]

Test suite 100% verde

Logs forenses consistentes

ZIP seguro aprovado

MOVE/COPY idempotentes

ACL validadas

Aleatorização de tmpdirs funcional

VLAN isolation validada

Documentação atualizada
