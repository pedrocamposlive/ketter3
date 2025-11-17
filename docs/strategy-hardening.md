1. Introdução
1.1. Propósito do Documento

Este documento define, com profundidade máxima, as diretrizes de hardening, segurança operacional, proteção de dados, controle de acesso, auditoria, isolamento inter-VLAN e compliance TPN/MPA da arquitetura do Ketter — um sistema de transferência automatizada de arquivos utilizado em ambientes de pós-produção, dublagem e finishing em estúdios com segmentação de rede.

1.2. Escopo

Este strategy cobre:

Watchers

Engines MOVE/COPY

Empacotamento ZIP seguro

Sanitização avançada

Hashing e integridade

Forensics logs

Circuit-breakers

Race-condition prevention

Inter-VLAN secure execution

ACL / POSIX / Samba

Isolamento entre ingest → dublagem → QC → delivery

Padrões de estúdios Burbank

Compliance TPN/MPA

Auditorias automáticas

Hardening de scripts e CLI

Respostas a falhas

1.3. Princípios Fundamentais
A — Zero Trust Filesystem

Nenhum arquivo é confiável até passar por:

sanitização

verificação de volume

hashing

validação de integridade

ACL enforcement

B — Pipeline Segregado

Caminhos e VLANs não podem se cruzar.
O watcher de uma VLAN não acessa a outra.

C — Execução Determinística

Todas as etapas devem produzir outputs previsíveis.

D — Fail-Safe Always

Em qualquer erro:

Transferência aborta

Logs são preenchidos

Nenhum arquivo parcial é deixado no destino

E — Observabilidade Total

Cada passo gera logs forenses com:

timestamp UTC

id de transferência

id de máquina

id de VLAN

hash original/destino

resultado da ação

2. Cenário Real TPN/MPA
2.1. Estúdios em Burbank

Ambientes dominantes:

Warner

Walt Disney

Netflix

Sony

NBCUniversal

Paramount

Todos seguem variações das mesmas regras:

Segmentação de rede entre setores

Restrição de montagem cross-VLAN

Transfer nodes

Logging forense

Trabalhos movidos através de automação (não via usuários)

2.2. Exigências Recorrentes

Nenhuma permissão de escrita em VLANs não pertencentes ao setor

Hashing duplo: SHA256 e SHA512 quando necessário

Logs imutáveis

Operações idempotentes

Volume whitelisting

Proibição de symlinks

Execução mínima privilegiada

Auditoria semestrais

Sem tráfego SMB cruzado

Tudo deve estar com clocks sincronizados

UTC everywhere

3. Arquitetura do Hardening
3.1. Camadas de Endurecimento

O hardening é dividido em cinco camadas:

Filesystem Hardening

Operational Hardening

Security Hardening

Network / VLAN Hardening

Audit / Forensics Hardening

3.1.1. Filesystem Hardening

Inclui:

Sanitização avançada de nomes

Bloqueio de caracteres perigosos

Normalização Unicode NFC/B

Remoção de metadados invisíveis

Proteção contra traversal (.., %2e%2e, etc.)

Symlink refusal

Restrição de tamanho de arquivo no ZIP

Controle sobre diretórios temporários

3.1.2. Operational Hardening

Inclui:

Freeze states

Retry inteligente

Circuit-breakers

Timeouts

Locks com watchdogs

Zonas de operação isoladas

Execução read-only para watchers

3.1.3. Security Hardening

Inclui:

ACL e permissões POSIX/SAMBA

Validação de permissões antes do MOVE

Hashing antes e depois

Execução sem privilégios elevados

Randomização de tmpdirs

3.1.4. Network / VLAN Hardening

Inclui:

Segmentação rígida

Transfer Nodes

Zero SMB cross-VLAN

Comunicação via pipe local ou endpoint isolado

3.1.5. Forensics Hardening

Inclui:

Logs estruturados JSON

Hash de logs (opcional blockchain local)

IDs únicos de fluxo

Identidade de máquina

Auditoria diária

4. Hardening do Watcher
4.1. Ciclo Hardening
4.1.1. O watcher nunca escreve no destino diretamente

Ele apenas aciona a engine.

4.1.2. Hardening aplicado

Timeouts

Loop seguro (stop hooks)

Detecção de milhares de arquivos

ZIP sem compressão

Filtragem de arquivos invisíveis

Normalização Unicode

Circuit breaker por volume

Logging granular

5. Hardening MOVE/COPY Engine
5.1. Sanitização de caminhos

Antes de qualquer movimento:

realpath

volume whitelist

regex de allowed patterns

unicode normalize

bloqueio de caracteres proibidos

comparação canonicalizada

5.2. Modo MOVE

Regras:

atomicidade: não deixa partials

rollback automático

verificação no destino antes da remoção

hash-duplo opcional

5.3. Modo COPY

Regras:

validação antes

validação depois

sem race conditions

offset validation

5.4. ZIP Secure Mode

ZIP sem compressão (store only)

Normalização de headers

Proibição de paths “../../”

max-size por arquivo

metadata scrubbing

tmpdir randomizado

validação de conteúdo após unzip

6. ACL / Permissões / POSIX / Samba
6.1. Princípios

Least privilege

Pastas de entrada só leitura

Pastas de saída só escrita pela engine

Setgid nos destinos

Sticky para evitar cross-write

Samba com create masks restritivas

6.2. Conformidade TPN

A VLAN nunca pode acessar pastas de outra VLAN via SMB

Somente Transfer Nodes intermediam

Logs devem registrar usuário + VLAN + ação

7. Hashing e Integridade
7.1. Hashing Obrigatório

SHA-256 antes e depois.

7.2. Hashing Opcional

SHA-512, quando:

material crítico

produção original

países com regulamentação adicional

7.3. Regras

Hash do ZIP antes de transferir

Hash da pasta extraída

Hash do destino

Logs contendo ambos

8. Forensics Logging
8.1. IDs únicos

Cada ação gera:

transfer_id

vlan_id

machine_id

job_id

hash_pre

hash_post

timestamp_utc

resultado

8.2. Imutabilidade

Logs antigos são rotacionados e assinados digitalmente.

9. Auditoria TPN/MPA
9.1. Ciclo

Logs diários

Alertas automáticos

Validação manual mensal

Validação semestral oficial

9.2. Itens auditáveis

acessos

hashes

movimentos

falhas

volumes

permissões

inter-VLAN

watchers

10. Hardening Inter-VLAN
10.1. Execução

Cada VLAN tem:

watchers próprios

engines próprias

restrições próprias

10.2. Transfer Node

É o único componente com permissão para interagir com múltiplas VLANs.

Regras:

Execução isolada

Logging segregado

Ações assíncronas

11. Resiliência / Fail-Safe
11.1. Mecanismos

rollback atômico

revalidação pós-falha

retry diário

journal de ações

circuit-breaker global

12. Testes de Hardening
12.1. Testes Unitários

sanitização

hashing

engine

zip handler

12.2. Testes de Integração

watchers

inter-VLAN

engine MOVE/COPY

rollback

12.3. Testes de Segurança

traversal

symlink

ACL

permissão negada

hash mismatch

13. Critérios de Conclusão

A fase é considerada completa quando:

Todos os itens do state-hardening estão marcados

Test suite verde

Logs aprovados

Falhas auditadas

ZIP seguro validado

Execução inter-VLAN em simulação confirmada

Documentação sincronizada

Scripts validados

14. Finalização

Ao finalizar a fase:

strategy-hardening.md deve estar sincronizado com os patches aplicados

blueprint-hardening.md deve estar funcional para o Codex CLI

state-hardening.md deve estar 100% concluído

Uma release alpha-hardening deve ser marcada no Git
