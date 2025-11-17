KETTER 3.0 — ENHANCE GUIDE

Versão 1.0 — Plano de Implementação de Melhorias

Data: 2025-11-12
Autor: Eng. Coordenação Técnica
Baseado em: Ketter 3.0 – Senior Dev Code Audit Report

Objetivo

Este documento instrui a execução das melhorias identificadas no relatório de auditoria, priorizando segurança, consistência transacional, resiliência operacional e observabilidade no módulo de Transferência (COPY/MOVE).

Estrutura de Execução
FASE 1 — Hotfixes Críticos (antes do deploy em produção)

Prazo sugerido: 48 h
Responsável: Backend Core Team

#	Ação	Arquivo(s)	Descrição técnica	Validação
1	Sanitização de paths	schemas.py / copy_engine.py	Implementar sanitize_path() com os.path.realpath() e whitelist (volumes permitidos). Bloquear .. traversal e symlinks.	Teste unitário com paths maliciosos
2	Lock de concorrência em MOVE	worker_jobs.py / database.py	Implementar SELECT FOR UPDATE ou lock baseado em source_path_hash. Impedir que dois jobs atuem no mesmo arquivo.	Teste de corrida com 2 workers
3	Rollback transacional	worker_jobs.py	Usar try/except/finally + session.rollback() em falhas parciais. Garantir atomicidade.	Teste de falha em meio de transferência
4	Verificação pós-deleção	copy_engine.py	Após checksum, validar destino legível antes de remover origem.	Teste de simulação com falha no destino
5	CORS restrito	main.py	Restringir origens a domínios confiáveis (config via env).	Curl externo de origem não autorizada
6	Circuit breaker em Watch Mode	worker_jobs.py	Adicionar parâmetros max_cycles, timeout e graceful_exit().	Teste contínuo de 1 h sem novos arquivos
FASE 2 — Estabilidade e Recuperação (próximo sprint)

Prazo sugerido: 1 semana
Responsável: Core + Infra

#	Ação	Descrição	Implementação sugerida
1	Retry automático	Retries com backoff exponencial (3×) em falhas transitórias (I/O, rede).	Decorador @retry(...) + logging estruturado
2	Logging estruturado	Substituir print() por logging (JSON formatter).	Logging por módulo + níveis configuráveis
3	Controle de espaço atômico	Check de disco integrado à operação.	Lock temporário + verificação dentro do job
4	Testes de rollback e falhas	Simular falhas de disco, rede, kill de processo.	Pytest + fixtures de falha
5	Cobertura > 80 %	Expandir testes unitários + integração.	Cobertura verificada com pytest --cov
6	Graceful shutdown	Sinal SIGTERM encerra watchers ativos com persistência de estado.	Handler + checkpoint JSON
FASE 3 — Performance & Escalabilidade

Prazo sugerido: 2–3 semanas
Responsável: Backend Optimization Team

#	Melhoria	Ação
1	Parallel checksum	Calcular hash enquanto copia (pipeline I/O + CPU).
2	sendfile()	Usar zero-copy em Linux para ganho de throughput.
3	Batch DB Commits	Acumular 50 logs e commitar em lote.
4	Connection pool tuning	Ajustar pool_size para >= 10.
5	Benchmarks regressivos	Script bench_transfer.py – 1000 arquivos × 1 GB.
6	Async audit flush	Registrar logs no Redis e gravar em batch no Postgres.
FASE 4 — Segurança e Compliance

Prazo sugerido: 1 semana (pós hotfix)
Responsável: Security Team

#	Ação	Objetivo
1	Symlink check	Rejeitar symlinks fora do volume permitido.
2	Rate limiting	Evitar DoS por uso abusivo de API.
3	Autenticação JWT	Bloquear endpoints públicos (fase B).
4	Log sanitization	Remover dados sensíveis antes de gravar.
FASE 5 — Observabilidade e Manutenção Contínua

Responsável: Infra & DevOps

Área	Implementação
Prometheus / Grafana	Exportar métricas de jobs e throughput.
WebSocket Progress	Stream em tempo real no frontend.
Chaos Testing	pytest-chaos para falhas aleatórias.
Documentação	Atualizar README + docs/architecture.png
Review mensal	Rodar novo “Mini Audit Report” automático.
Boas Práticas de Execução

Rastreabilidade: Cada melhoria deve ser vinculada a um commit com tag enhance-<id>

Rollback seguro: Testar rollback antes de merge em main

Logs limpos: Validar que mensagens sensíveis não sejam expostas

Revisão cruzada: Todo patch de MOVE mode deve ser revisado por 2 desenvolvedores

Validação pós-deploy: Rodar integration_test_suite.sh e comparar checksums

Resultado Esperado

Após seguir este plano, o Ketter 3.0 deve atingir:

Dimensão	Meta	Esperado
Segurança	Path traversal mitigado	
Confiabilidade	MOVE atomic & rollback ok	
Observabilidade	Logs estruturados + métricas	
Performance	+20 % I/O e -30 % CPU hash	
Test coverage	≥ 80 % (total)
