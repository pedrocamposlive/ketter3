KETTER — HARDENING STATE
Fase 2 — Segurança, Integridade e Conformidade TPN/MPA
Documento de Estado — Execução via Codex CLI
0. Objetivo

Este documento lista TODAS as tarefas atômicas da fase de hardening.
Cada tarefa deve ser executada em ciclos independentes via Codex, seguindo o blueprint-hardening.md.

Regras:

Codex executa uma única tarefa por ciclo.

Sempre que concluir, deve atualizar este arquivo.

Todas as tarefas marcadas [ ] serão executadas.

Quando marcadas [x], devem conter timestamp UTC e breve evidência.

1. Filesystem Hardening
1.1. Sanitização Avançada

- [x] Criar sanitização unicode NFC/NFD para todos os paths — 2025-11-14T20:56:15+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

 Criar sanitização unicode NFC/NFD para todos os paths
 [x] Implementar bloqueio de caracteres perigosos (regex enterprise) — 2025-11-14T21:25:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

 Implementar bloqueio de caracteres perigosos (regex enterprise)

 - [x] Implementar normalização unicode fold (lowercase canonical) — 2025-11-14T21:42:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)
 - [x] Criar função de canonicalização de paths inter-VLAN — 2025-11-14T21:50:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)
- [x] Bloquear whitespace invisível e caracteres especiais ilegais — 2025-11-14T22:05:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)
Implementar normalização unicode fold (lowercase canonical)

 Criar função de canonicalização de paths inter-VLAN

 Testes unitários de sanitização (security/test_sanitize.py)

1.2. Proteção contra Traversal

 Implementar bloqueio total de .., %2e%2e, encoded traversal

 Verificar realpath canônico antes de transferir

 Criar testes de traversal

1.3. Symlink Protection

- [x] Bloquear qualquer symlink na origem — 2025-11-14T22:35:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

 Bloquear symlinks dentro de ZIP

 Criar testes

1.4. Volume Whitelisting

- [x] Expandir whitelist para nível de VLAN — 2025-11-14T22:45:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Criar testes para volume inválido — 2025-11-14T22:45:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Permitir override somente em modo Transfer Node — 2025-11-14T22:45:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

1.5. tmpdir Hardening

- [x] Criar tmpdir randomizado seguro — 2025-11-14T22:55:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)
- [x] Bloquear previsibilidade — 2025-11-14T22:55:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)
- [x] Criar testes — 2025-11-14T22:55:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

2. ZIP Secure Hardening
2.1. ZIP Store-Only

- [x] Garantir modo STORE-only em compressão — 2025-11-14T23:10:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Criar validação de header ZIP — 2025-11-14T23:10:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Criar testes correspondentes — 2025-11-14T23:10:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

2.2. ZIP Path Protection

- [x] Bloquear extração de arquivos com / ou ../ — 2025-11-14T23:20:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Implementar scanner de headers — 2025-11-14T23:20:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Criar testes de ZIP traversal — 2025-11-14T23:20:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

2.3. ZIP Metadata Scrubbing

- [x] Remover timestamps MACOS/NTFS — 2025-11-14T23:30:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Normalizar metadados ao extrair — 2025-11-14T23:30:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Criar testes — 2025-11-14T23:30:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

2.4. ZIP Size Hardening

- [x] Implementar limite de tamanho por arquivo — 2025-11-14T23:45:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Implementar limite total do ZIP — 2025-11-14T23:45:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Criar testes de limite — 2025-11-14T23:45:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

2.5. ZIP Hashing

- [x] Gerar SHA256 do ZIP antes da transferência — 2025-11-14T23:55:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Validar SHA256 pós-extração — 2025-11-14T23:55:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

- [x] Criar testes — 2025-11-14T23:55:00+00:00 (tests: `DATABASE_URL=sqlite:///./test_state.db PYTHONPATH=. pytest`)

3. MOVE/COPY Hardening (Engine)
3.1. Atomicidade

 Implementar atomic rename para concluir operações

 Garantir rollback com idempotência verdadeira

 Criar testes de rename/rollback

3.2. Idempotência

 Validar que tarefas repetidas não criam duplicatas

 Criar testes

3.3. Pre-Validation

 Hash-before

 Permissão-before

 Volume-before

 Criar testes

3.4. Post-Validation

 Hash-after

 Permissão-after

 Volume-after

 Testes

3.5. Partial Write Detection

 Criar mecanismo de detecção de escrita incompleta

 Criar testes de falha simulada

3.6. Circuit Breaker

 Criar circuito de proteção por volume/destino

 Criar testes

4. Watcher Hardening
4.1. Safe Loop

 Implementar thời-meout para loop

 Implementar ciclo com supervisão

 Testes de watchdog

4.2. File Filtering

 Reforçar filtro para arquivos invisíveis complexos

 Adicionar filtros para arquivos de metadata especiais

 Criar testes

4.3. Inter-VLAN Mode

 Criar watcher restrito por VLAN

 Testes de VLAN isolation

4.4. Multi-file Detection

 Garantir performance para >50.000 arquivos

 Criar testes large-scale

5. ACL / Permission Hardening
5.1. POSIX ACL

 Verificar ACL na origem antes do MOVE

 Validar ACL no destino após MOVE

 Testes de ACL

5.2. Samba ACL

 Criar enforce de create mask

 Testar via simulação

 Validar logs

5.3. Least Privilege

 Validar execução sem privilégios elevados

 Criar testes

6. Network / VLAN Hardening
6.1. Transfer Node Isolation

 Criar módulo app/core/vlan_router.py

 Criar regra: watchers não acessam VLAN de destino

 Criar testes de VLAN cross-block

6.2. VLAN Binding

 Cada instância do Ketter deve informar vlan_id

 Criar testes

6.3. Proibição Cross-SMB

 Testar operação simulada

 Documentar logs

7. Forensics Hardening
7.1. Logs Estruturados

 Criar módulo forensics app/security/forensics.py

 Inserir IDs únicos em cada ação

 Testes de logging forense

7.2. Log Hashing

 Hashinar cada log diário

 Testes

7.3. Auditoria Diária/Mensal/Semestral

 Criar módulo de auditoria automática

 Criar testes

8. Auditoria TPN/MPA
8.1. Requisitos

 Validar logs TPN/MPA

 Validar segregação de VLAN

 Validar atomicidade dos MOVE/COPY

 Validar controle de permissões

 Testes automatizados

9. Finalização da Fase Hardening
9.1. Critérios

 Todos os itens marcados como [x]

 Test suite 100% verde

 Documentação revisada

 state-hardening finalizado

 Criar release ketter-hardening-alpha

10. Registro Automático

Ao concluir cada item:

Marcar [x]

Registrar data/hora UTC

Detalhar testes executados

Descrever resultado

Inserir commit hash

### PATCH REMOÇÃO DE EMOJIS E SÍMBOLOS



- Todas as ocorrências das faixas Unicode U+1F300–U+1F6FF, U+1F900–U+1F9FF, U+1FA70–U+1FAFF, U+2600–U+26FF, U+2700–U+27BF foram removidas dos arquivos `.py`, `.js`, `.jsx`, `.css`, `.md`, `.json` e `.sh` por meio de script controlado.
- Removemos também as sequências `:-)` e `;-)` para eliminar winks textuais, mantendo logs e mensagens intactos.
- O repositório agora exibe apenas texto ASCII/UTF básico nos pontos auditados, alinhado à política de hardening.
