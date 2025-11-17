# Ketter — Hardening TPN/MPA  
Versão 1.0  
Escopo: Segurança, Isolamento, Auditoria e Compliance de Estúdio

---

## 1. Objetivo
Elevar o Ketter ao nível de conformidade operacional exigido por estúdios Burbank seguindo práticas TPN/MPA:

- Zero trust entre VLANs  
- Cadeia de confiança por hashing  
- Auditoria forense  
- Logs estruturados  
- Atomicidade e rollback  
- Whitelist de volumes  
- Path sanitization rigoroso  
- Execução isolada (automation node)  

---

## 2. O Papel do Ketter no Ambiente TPN
Em estúdios profissionais:

- Ingest, Dublagem, QC e Delivery ficam em **VLANs isoladas**  
- Sem cross-mounts  
- Automação sempre opera como **nó isolado**  
- Toda transferência deve ser **auditável e verificável**

Ketter é o “automation node” entre zonas, respeitando isolamento.

---

## 3. Princípios de Hardening

### 3.1 Zero Trust + Isolation
- Nenhum acesso cruzado de volumes entre VLANs  
- Cada node executa apenas dentro da própria zona  

### 3.2 Cadeia de Confiança
- Hash pré e pós transferência  
- Manifest com: nome, tamanho, hash, horário, origem e destino  

### 3.3 Logs Forenses
- JSON padronizado  
- timezone UTC  
- event_class  
- vlan_source / vlan_target  
- operador/automation_id  

### 3.4 Path Sanitization
- realpath obrigatório  
- negar symlinks  
- bloquear unicode trick  
- negar executáveis  
- negar arquivos ocultos  
- validar extensão e inode antes e depois  

### 3.5 Execution Hardening
- atomicidade  
- rollback completo  
- retry com jitter  
- circuit-breaker  

---

## 4. Arquitetura Hardening

### Fluxo MOVE/COPY (TPN)
1. Detecta →  
2. Sanitize →  
3. Hash pré →  
4. (Opcional) empacota →  
5. Move →  
6. Hash pós →  
7. Valida →  
8. Gera audit-trail →  
9. Commit →  
10. Libera próximo nó (multi-hop)

### Multi-Hop Example
Ingest → Dub → QC → Delivery  
Sempre via nós isolados.

---

## 5. Implementação por Camadas

### 5.1 Whitelist de Volumes
- lista controlada no `ketter.config.yml`  
- validação de permissões  
- validação de owner e grupo  
- proibição de bind mounts indevidos  

### 5.2 Sanitização Avançada de Paths
- validação de inode antes/depois  
- bloquear renomeios durante transferência  
- negar nomes proibidos  
- negar namespace oculto  

### 5.3 Hash Chain
- SHA-256  
- manifest pré/pós  
- auditoria do ciclo completo  

### 5.4 Logs Forenses
- JSON estruturado  
- arquivos diários  
- evento por ação dentro do fluxo  

### 5.5 Auditoria Imutável
- registros não editáveis  
- assinatura de manifest  
- cadeia de custódia  

---

## 6. Testes Obrigatórios (Hardening Suite)
- path traversal  
- symlink swap  
- race conditions  
- checksum mismatch  
- rollback atomic  
- partial write simulation  
- circuit breaker  
- multi-hop isolation  
- volume whitelist  
- hidden file rejection  

---

## 7. Roadmap Hardening
1. Implementar Sanitization Layer  
2. Implementar Whitelist de Volumes  
3. Implementar Hash Chain  
4. Implementar Audit Trail  
5. Implementar Multi-Hop Mode  
6. Implementar Modo Isolado (Air-Gap Parcial)  
7. Criar Hardening Test Suite  
8. Integrar com state.md  
9. Finalizar sprint com CI 100% verde  

---

## 8. Execução com Codex
Todos os ciclos serão executados via:

```
codex run "Read STRATEGY_PROMPT.md, HARDENING_TPN_MPA_STRATEGY.md, blueprint-hardening.md. 
Identify the next pending task in state-hardening.md.
Execute using the full blueprint cycle."
```

---

## 9. Resultado Esperado
O Ketter torna-se um **automation node corporativo**, alinhado com o padrão TPN/MPA, apto para:

- rastreamento
- auditoria
- isolamento
- confiabilidade
- operação multi-VLAN

---


