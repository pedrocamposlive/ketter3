strategy.md

Ketter / Sefirot — Documento Mestre de Estratégia, Arquitetura e Governança
Versão 1.0

1. Introdução
1.1 Propósito do Documento

Este documento define a estratégia completa do Ketter/Sefirot: arquitetura, operação, fluxo de transferência, padrões técnicos, compliance, governança e integração com assistentes (Codex CLI).
Ele é o documento mestre. Todos os demais .md (README, blueprint, state, enhance) derivam dele.

1.2 Escopo do Ketter / Sefirot

O Ketter é um sistema de automação de transferências entre pastas e servidores segmentados por VLANs, adotado em ambientes de pós-produção e dublagem com exigências TPN/MPA.
Inclui:

Watcher contínuo

Engines COPY e MOVE

Empacotamento ZIP sem compressão

Auditoria e logs

Conformidade com isolamento de rede

Operação contínua e segura

1.3 Princípios Fundamentais

Simplicidade operacional: entregar automação sólida e fácil de operar.

Confiabilidade e segurança: nunca perder arquivos, nunca criar inconsistência.

Execução contínua: processo permanente e autônomo.

Compliance TPN/MPA: segurança de fluxo inter-VLAN.

Auditoria e rastreabilidade: logs completos, eventos, checksums, histórico.

2. O Problema: Transferências em Estúdios TPN/MPA
2.1 Cenário Real em Burbank

Estúdios de dublagem e pós (VSI, VOXX, Point.360, Deluxe, Warner) operam com VLANs isoladas para evitar crossing SMB e fuga de material confidencial.

2.2 Segmentação por VLAN

Ambientes típicos:

VLAN 10 – Ingest

VLAN 20 – Dublagem / Áudio

VLAN 30 – VFX

VLAN 40 – QC

VLAN 50 – Delivery

2.3 Restrições de segurança

Sem montagens cruzadas via SMB/NFS.

Somente Automation Nodes podem ter múltiplas montagens.

Todo fluxo deve ter trilha de auditoria.

2.4 Dor operacional que o Ketter resolve

Ausência de pipelines de transferência.

Falta de logs confiáveis.

Dependência de operadores.

Falhas intermitentes.

Múltiplos serviços desconectados.

Necessidade de watchers especializados.

Ausência de validação pós-transferência.

3. Visão Geral do Sistema Ketter
3.1 O que é o Ketter

Um Automation Node com watchers, engine de transferência e auditoria.
Ele monitora pastas, movimenta arquivos, valida integridade e produz logs estruturados.

3.2 Arquitetura de Alto Nível

Watcher → Detecta

Validator → Confere integridade

Engine COPY/MOVE

Compressor (opcional)

Auditor (logs)

Cleaner (MOVE)

Observabilidade futura

API futura

3.3 Componentes Principais

Watcher contínuo

Engine COPY

Engine MOVE

Empacotamento ZIP

Desempacotamento no destino

Auditor de eventos

Logs estruturados

Futuro: API, UI, RBAC, métricas

4. Ciclo de Pastas (Folder Cycle)
4.1 Modelo clássico em estúdios

INGEST → STAGING → DUBBING → QC → DELIVERY

4.2 Adaptação ao Ketter

Origem(s) e destino(s) configuráveis via YAML.

4.3 Estados de uma Transferência

Detectado

Validado

Empacotado (quando pasta com muitos arquivos)

Transferindo

Verificando (checksum)

Concluído

Failed / Retry

4.4 Fluxo MOVE e COPY

COPY: mantém origem
MOVE: deleta origem apenas após verificação + confirmada integridade

5. Arquitetura Técnica (Inter-VLAN)
5.1 Automation Node

É o único servidor com montagens múltiplas.
Todos os fluxos passam por ele.

5.2 Zonas de Rede

Exemplos:

/mnt/ingest

/mnt/dub

/mnt/qc

/mnt/delivery

5.3 Regras TPN/MPA

Nada de SMB cross-VLAN direto em workstations.

Hashing obrigatório.

Logs por operação.

Acesso mínimo (least privilege).

Monitoramento contínuo.

5.4 Como o Ketter preserva o compliance

Opera sozinho como node isolado.

Implementa hash SHA-256.

Mantém logs imutáveis.

Evita montagem cruzada irregular.

Faz auditoria completa de eventos.

6. Estado Atual do Projeto (state.md)
6.1 Resumo do estado atual

Watcher, copy/move, zip/unzip funcionando.
Faltam robustez, logs, validação, isolamento, documentação, auditoria.

6.2 Módulos implementados

Watcher básico

COPY/MOVE básico

ZIP sem compressão

Unzip no destino

Estrutura inicial de pastas

state.md reestruturado

6.3 Módulos em desenvolvimento

Logs estruturados

Auditor de eventos

Retry/rollback

YAML config centralizado

6.4 Módulos planejados

API

Observabilidade

RBAC com AD

UI PySide6

Plugins de automação

6.5 Mapeamento state.md → strategy.md

(state.md lista tarefas operacionais; strategy define estratégia e arquitetura.)

6.6 Riscos e lacunas

Watcher não resiliente

COPY/MOVE sem rollback

Logs insuficientes

Falta de auditoria

Falta de validação sistemática

7. Estrutura do Repositório
7.1 Pastas

src/

docs/

logs/

configs/

tests/

scripts/

7.2 Arquivos .md

README.md

blueprint.md

state.md

enhance.md

strategy.md

7.3 Relação entre documentos

strategy.md → Manda em tudo

README.md → Onboarding

blueprint.md → Executor

state.md → O que está em andamento

enhance.md → Ideias/futuro

8. Watcher
8.1 Estrutura

Uso de watchdog

Fila interna

Debounce

Tratamento de milhares de arquivos

8.2 Estados

Detect → Queue → Validate → Process

8.3 Resiliência

auto-retry

auto-respawn

processamento em fila

8.4 Detecção massiva

Zip sem compressão + extrair no destino.

8.5 Empacotamento

zipfile
Sem compressão
Metadados preservados

8.6 Desempacotamento

Destino → validação → remoção do ZIP

8.7 Undo / rollback

Futuro: reverter operações incompletas

8.8 Retry

Implementar backoff exponencial

9. Engine de Transferência
9.1 COPY

Cópia com validação de tamanho + hash

9.2 MOVE

COPY + DESAPAREAR origem após validação

9.3 Modo de empacotamento

Ativo para pastas com muitos arquivos

9.4 Validação pós-transferência

SHA-256 obrigatório

9.5 Checksums

SHA-256 preferencial
MD5 opcional

9.6 Mapeamento de diretórios

Config YAML define origens/destinos

9.7 Problemas conhecidos

Falha silenciosa de disco

Timeout sem retry

Falta de rollback

9.8 Recomendações

Atomic writes

Rename only on success

Delete only after hash match

10. Logs & Auditoria
10.1 Logs estruturados (JSON)

Registrar:
arquivo, origem, destino, tamanho, hash, operador, estado, timestamps

10.2 Evento por operação

detect

prepare

copy

verify

complete

fail

10.3 Log rotation

Rotação por dia ou tamanho

10.4 Alertas

Integrável a Slack, Teams, email

10.5 Logging TPN/MPA

Imutáveis, completos, rastreáveis

10.6 SIEM

Compatível com Splunk / Elastic

11. Boas Práticas TPN/MPA
11.1 Automation Nodes

Sempre centralizar transição inter-VLAN.

11.2 Hash validation

SHA-256 obrigatório.

11.3 Air gap parcial

Somente o Automation Node transita entre redes.

11.4 Controle de acesso

ACL mínima.

11.5 Nada de SMB cross-VLAN

Somente Automation Node monta.

11.6 Hardening

desativar serviços desnecessários

firewall restritivo

ACL interna

12. Checklist Técnico

Infra
FS
ACL
Montagens
Variáveis
Estrutura mínima
Logs
Watcher
Transferência
Hashing
Retry
Rollback
Serviço systemd
Observabilidade

13. Roadmap Evolutivo
13.1 Fase 1 — Estabilização

Watcher, engine, logs, zip, paths

13.2 Fase 2 — Observabilidade

Prometheus + Grafana

13.3 Fase 3 — API

GET/POST transfers + health

13.4 Fase 4 — RBAC

AD/LDAP

13.5 Fase 5 — UI

PySide6 ou Web

13.6 Fase 6 — Plugins

Automação externa

14. Guia para Assistentes (Codex CLI / ChatGPT)
14.1 Como interpretar o repositório

strategy → README → blueprint → state → enhance

14.2 Ordem de leitura

Sempre seguir em cascata.

14.3 Documento mestre

strategy.md manda em tudo.

14.4 Como gerar arquivos

Usar blueprint.md para tarefas.

14.5 Como seguir o blueprint

Cada item do blueprint é uma sprint curta.

14.6 Estilo de commit

Tipo convencional:
feat, fix, docs, refactor

14.7 Manutenção automática do state.md

Assistentes devem marcar tarefas concluídas.

14.8 Sugestão de melhorias

Registrar em enhance.md

15. Metodologia de Desenvolvimento
15.1 Fluxo Git

main → develop → feature branches

15.2 Branches

feature/, fix/, docs/

15.3 Documentação

Tudo via .md, sempre atualizado.

15.4 Princípios

Clareza, logs, segurança, rastreabilidade.

15.5 Código

Python 3.10+, typing, modular.

15.6 Testes

Unitários e testes de integração.

15.7 Auditorias

Code review regular.

16. Apêndice
16.1 Modelos de logs

JSON estruturado

16.2 Modelos de eventos

event, ts, file, user, action

16.3 Config files

config.yaml

16.4 Estrutura mínima de transferência

source, dest, state, hash, retry

16.5 Diagramas

docs/architecture.png
