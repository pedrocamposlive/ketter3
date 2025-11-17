# Ketter 3.0 — UI Visual Spec (Manus Design Reference)
Versão: 1.0
Origem: Blueprint gerado via Manus IA (Dark Enterprise UI)

---

## Objetivo
Este documento consolida a visão visual oficial do Ketter 3.0, gerada via Manus IA, servindo como referência para:
- Implementação da UI
- Definição de tema
- Construção de componentes
- Padronização visual entre dashboards, logs, settings e auditoria

---

## Tema Geral
**Dark Enterprise**, inspirado em:
- Palantir Foundry
- Datadog Dark
- Splunk Enterprise
- AWS Console (tema dark)
- Houdini Solaris

### Paleta
- Fundo primário: `#0C0E12`
- Fundo elevado (cards): `#12151C`
- Borda suave: `#1A1D25`
- Texto primário: `#E8ECF0`
- Texto secundário: `#A5AAB2`
- Destaque cobalto: `#3A8BFF`
- Destaque ciano: `#36C6F0`
- Sucesso: `#4CAF50`
- Warning: `#D0A036`
- Falha: `#D84545`
- Info: `#3A8BFF`

### Tipografia
- Inter
- IBM Plex Sans
- JetBrains Mono (código, hashes, logs)

Tamanhos:
- H1: 24px
- H2: 20px
- H3: 16px
- Body: 14px
- Mono: 13px

### Grade
- Grid baseado em 12 colunas
- Spacing tokens: 4, 8, 12, 16, 24, 32px
- Cards com padding 16px
- Gaps horizontais entre cards: 16px
- Gaps verticais: 20px

---

## Componentes Principais

### 1. KPI CARD (Dashboard)
Cada card contém:
- Título pequeno (texto secundário)
- Valor grande (texto primário)
- Badge de status (opcional)
- Micro-gráfico (opcional)

Exemplos:
- Transferências ativas
- Transferências concluídas 24h
- Falhas 24h
- Hash Verification
- ZIP Smart Enabled

---

### 2. Painel de Logs Estilo SIEM
- Linha única por log
- Timestamp UTC (mono)
- Categoria com badge de cor
- Descrição curta
- Ordem decrescente
- Rolagem vertical

Badges:
- success
- failure
- hash mismatch
- security alert
- rollback
- info

---

### 3. Throughput Chart (24h)
- Gráfico de linha
- Eixo X = hora UTC
- Eixo Y = MB/s
- Linhas azul-cobalto
- Pontos desabilitados
- Linha suave com curva

---

### 4. MOVE vs COPY Donut Chart
- Donut circular
- MOVE = azul
- COPY = ciano
- Percentual no centro

---

### 5. VLAN Map
Representação visual:

[ VLAN INGEST ] → [ VLAN DUBLAGEM ] → [ VLAN QC ] → [ VLAN DELIVERY ]
(Automation Node isolando tráfego)

yaml
Copy code

Cada bloco com:
- Título
- Descrição
- Cor leve diferenciada
- Borda fina
- Flecha minimalista entre elas

---

### 6. Transfer Detail View
Card com:
- Origem
- Destino
- Hash SHA-256
- Zip Smart enabled/disabled
- Timestamps UTC
- Status badge
- Logs individuais
- Botão de exportar PDF

---

### 7. Auditoria & Timeline Forensic
- Linha vertical
- Marcadores
- Evento (badge)
- Timestamp UTC
- Descrição
- Layout parecido com painel SIEM mas em timeline

---

### 8. Settings Page
Seções:
- Allowed Volumes
- Whitelist
- Worker Settings
- ZIP Smart Thresholds
- Logging Level

Componentes:
- Switches
- Checkboxes
- Dropdowns
- Fieldsets com títulos

---

## Conclusão
Este arquivo é a base visual oficial que o Codex deverá seguir na implementação da UI.  
Toda alteração futura deve ser rastreada no state-ui-visual.md.
