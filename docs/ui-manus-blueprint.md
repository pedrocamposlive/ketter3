# UI Manus Blueprint — Ketter 3.0
Fase avançada de integração visual Manus  
Escopo corporativo — alinhado ao design enterprise contemporâneo  
Status: Ativo

---

## 0. Objetivo da Fase Manus
Elevar a UI do Ketter 3.0 para padrão enterprise com:

- Palette Manus completa (cores, tons, cinzas, primários)
- Tipografia técnica
- Escalas de spacing, radius, shadow, transitions
- Layout global padronizado
- Dashboards refinados com KPIs, SIEM alerts, charts
- Páginas secundárias refinadas (Transfers, Audit, Settings, Health)
- Polimento final para apresentação executiva
- Preparação para exportar screenshots / arte final

Todas as tarefas executadas seguem o fluxo:

1. Criar/atualizar tokens em `theme.css` e `tokens.js`  
2. Ajustar componentes, pages, layout e App.css  
3. Atualizar `docs/state-ui-manus.md`  
4. Commits automáticos via Codex  

---

# 1. Theme Tokens — Manus
Escala completa para padronização visual.

### 1.1. Palette Manus
Status: DONE

### 1.2. Grayscale Manus  
Criar tons:  
`--ketter-gray-100 ... --ketter-gray-600`  
Usar nos backgrounds, bordas e textos secundários.

### 1.3. Tipografia Manus
Fontes principais: Inter / IBM Plex / JetBrains  
Tokens:  
`--ketter-font-body`  
`--ketter-font-heading`  
`--ketter-font-mono`  
Pesos: 300–600  
Tracking tokens.

### 1.4. Spacing Scale Manus
Tokens:  
`--ketter-space-xxs ... --ketter-space-xxxl`

### 1.5. Radius Scale Manus
Tokens:  
`--ketter-radius-sm/md/lg/pill`

### 1.6. Shadow Scale Manus
Tokens:  
`--ketter-shadow-1/2/3/focus`

### 1.7. Transition Scale Manus
Tokens:  
`--ketter-transition-fast/base/slow/focus/transform`

---

# 2. Global Layout Refinement
Aplicar estilo enterprise em todo o Ketter.

### 2.1. Grid Manus
Criar estrutura `grid-template-areas` para:
- header
- sidebar
- content
- footer (opcional)

### 2.2. Header Manus
- novo spacing  
- tipografia refinada  
- versão escura  
- status pill refinada  

### 2.3. Global spacing
Aplicar spacing scale em:
- cards
- sections
- grids
- headers
- hero rows

### 2.4. Responsividade
Breakpoints:  
- 1440px (desktop XL)  
- 1024px (desktop normal)  
- 768px (tablet)  
- 480px (mobile)

### 2.5. Container padrão
Criar:  
`.ui-container { max-width: 1440px; margin: auto; padding: var(--ketter-space-lg); }`

---

# 3. Dashboard Refinement

### 3.1. KPIs Manus
- bordas, sombras, tipografia refinada  
- mini-graph redesenhado  
- spacing hierárquico  

### 3.2. Throughput Chart Manus
- suavizar linhas  
- refinar legendas  
- aplicar tokens  

### 3.3. Donut Chart Manus
- novo contraste  
- labels refinados  
- hover transitions  

### 3.4. Status Grid
- bordas tokenizadas  
- severity colors  
- spacing vertical/horizontal  

### 3.5. Alerts Panel (SIEM)
- badges enterprise  
- hover/focus states  
- layout com colunas  
- timestamp refinado  

### 3.6. Hierarchical Spacing
Aplicar `space-lg → space-md → space-sm`

### 3.7. Typography Polish
Aplicar headers e tracking adequado.

---

# 4. Transfers Page

### 4.1. Layout Manus
- section headers  
- card-panel unificado  
- spacing hierárquico  

### 4.2. TransferCard  
- cores por severidade  
- radius  
- sombras  

### 4.3. TransferDetailsPanel
- bloco lateral  
- headers refinados  
- monoespaçado p/ SHA-256  

### 4.4. Jobs Grid
- colunas refinadas  
- severity colors  
- spacing das células  

---

# 5. Audit Page
### 5.1. Timeline Manus
- bullets  
- vertical line  
- spacing por evento  

### 5.2. Colors & severity
- success  
- fail  
- rollback  
- security alert  

### 5.3. Vertical Spacing  
Hierarquia:  
space-lg > space-md > space-sm  

### 5.4. Legibilidade
- tamanho  
- tracking  
- contraste previsto pela palette  

---

# 6. Settings Page
### 6.1. Fieldsets Manus
- bordas finas  
- radius sm  
- títulos limpos  
- tipografia técnica  

### 6.2. Grid  
Aplicar grid 2–3 colunas conforme largura.  

### 6.3. Inputs  
Aplicar tokens de:
- radius  
- sombras  
- transitions  

### 6.4. Layout enterprise  
Spaces / separadores / grupos funcionais.

---

# 7. Health Page
### 7.1. Metrics Grid  
- boxes com radius md  
- sombras leves  

### 7.2. Visual refinado  
- tokens de background  
- severity colors  

### 7.3. Typography  
- headings  
- monospace p/ valores técnicos  

---

# 8. Final Polish (Passagem Completa)
Checklist final executável:

1. Normalizar spacing entre cards  
2. Normalizar headers  
3. Normalizar radius e sombras  
4. Corrigir qualquer cor fora da paleta  
5. Revisar hover/active/focus  
6. Verificar tipografia  
7. Auditoria visual final  
8. Documentar patch final  

---

# 9. Release Prep
### 9.1. Criar pasta `/public/assets/manus`
### 9.2. Exportar screenshots oficiais
### 9.3. Atualizar README com seção “UI Manus Revamp”
### 9.4. Preparar build final (notar AÇÃO HUMANA NECESSÁRIA)

---

# 10. Regras do Blueprint
- Não comentar enquanto executa  
- Atualizar apenas o escopo da tarefa marcada  
- Atualizar state  
- Criar commit  
- Parar após commit  

---


