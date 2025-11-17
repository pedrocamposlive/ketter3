# UI Refactor - Watch Mode Radio Buttons

## O Problema Identificado

**Screenshot anterior mostra:**
```
 Watch Mode (wait for folder to stabilize)
 Continuous Watch (keep monitoring for new files)
```

**Problema:** Dois checkboxes separados causam confusão
- Usuário não sabe qual marcar
- Permite estados inválidos (ambos marcados, nenhum marcado)
- Falta clareza sobre a diferença
- UX ruim

---

## A Solução Implementada

**Novo design com Radio Buttons (Mutuamente Exclusivos):**

```
Watch Mode: (escolha UM)
○ No Watch (transfer immediately)
○ Watch Once (wait for stability, transfer once)
○ Watch Continuous (monitor indefinitely, auto-transfer)
```

**Vantagens:**
-  Apenas UMA opção selecionada (radio buttons)
-  Clareza sobre cada modo
-  Sem estados inválidos
-  Melhor UX (menos confusão)

---

## Arquivos Modificados

### 1. frontend/src/components/FilePicker.jsx
**Antes:**
```javascript
const [watchMode, setWatchMode] = useState(false)
const [watchContinuous, setWatchContinuous] = useState(false)
```

**Depois:**
```javascript
const [watchMode, setWatchMode] = useState('none')  // "none", "once", or "continuous"
```

**UI Antes:**
```jsx
<input type="checkbox" checked={watchMode} />
{watchMode && <input type="checkbox" checked={watchContinuous} />}
```

**UI Depois:**
```jsx
<input type="radio" value="none" checked={watchMode === 'none'} />
<input type="radio" value="once" checked={watchMode === 'once'} />
<input type="radio" value="continuous" checked={watchMode === 'continuous'} />
```

**Conditional Rendering:**
```jsx
{watchMode !== 'none' && (
  <div>Settle Time, Operation Mode, etc...</div>
)}
```

### 2. frontend/src/services/api.js
**Antes:**
```javascript
export async function createTransfer(
  sourcePath,
  destinationPath,
  watchMode = false,        // boolean
  settleTime = 30,
  operationMode = 'copy',
  watchContinuous = false   // boolean
) {
  // Enviar para API
}
```

**Depois:**
```javascript
export async function createTransfer(
  sourcePath,
  destinationPath,
  watchMode = 'none',       // string: "none", "once", "continuous"
  settleTime = 30,
  operationMode = 'copy'
) {
  // Converter para boolean que API espera
  const isWatchEnabled = watchMode !== 'none'
  const isWatchContinuous = watchMode === 'continuous'

  // Enviar para API
  body: JSON.stringify({
    watch_mode_enabled: isWatchEnabled,
    watch_continuous: isWatchContinuous ? 1 : 0,
    ...
  })
}
```

---

## Mapeamento de Estados

| Frontend | Backend | Significado |
|----------|---------|-------------|
| `watchMode = 'none'` | `watch_mode_enabled = false`<br/>`watch_continuous = 0` | Transfer imediatamente |
| `watchMode = 'once'` | `watch_mode_enabled = true`<br/>`watch_continuous = 0` | Watch 30s, transfer, stop |
| `watchMode = 'continuous'` | `watch_mode_enabled = true`<br/>`watch_continuous = 1` | Monitor forever |

---

## Comportamento da UI

### Quando `watchMode = 'none'`
```
 Source Path
 Destination Path
 Watch Mode: ● No Watch | ○ Watch Once | ○ Watch Continuous
 Settle Time (hidden)
 Operation Mode (hidden)
 CREATE TRANSFER
```

### Quando `watchMode = 'once'` ou `watchMode = 'continuous'`
```
 Source Path
 Destination Path
 Watch Mode: ○ No Watch | ● Watch Once | ○ Watch Continuous
 Settle Time: [30]
 Operation Mode: ● COPY | ○ MOVE
 CREATE TRANSFER
```

---

## Fluxo de Dados

```
FRONTEND (FilePicker)
  watchMode = "continuous"
    ↓
API Client (api.js)
  Converte: "continuous" → watch_mode_enabled=true, watch_continuous=1
    ↓
API (routers/transfers.py)
  Recebe: watch_mode_enabled=true, watch_continuous=1
  Cria: Transfer(watch_mode_enabled=1, watch_continuous=1)
    ↓
BACKEND (worker_jobs.py)
  if transfer.watch_continuous:
    watcher_continuous_job()
```

---

## Testes Realizados

 Frontend renderiza Radio Buttons corretamente
 Apenas UMA opção pode ser selecionada
 Settle Time aparece/desaparece corretamente
 Operation Mode aparece/desaparece corretamente
 API recebe dados corretos
 Backend processa corretamente

---

## Status Atual

-  Frontend refatorado
-  Containers reiniciados
-  UI atualizada
-  Backend compatível (sem mudanças necessárias)
-  Pronto para testes

---

## Como Testar

1. Abrir http://localhost:3000
2. Verificar que Watch Mode mostra 3 Radio Buttons
3. Selecionar cada opção:
   -  "No Watch" → Settle Time desaparece
   -  "Watch Once" → Settle Time aparece
   -  "Watch Continuous" → Settle Time aparece
4. Criar transfer com cada opção
5. Verificar que funciona corretamente

---

## Melhorias Futuras

- [ ] Adicionar ícones aos radio buttons (clareza visual)
- [ ] Adicionar tooltips explicativos
- [ ] Salvar última configuração (localStorage)
- [ ] Adicionar predefined presets ("Backup", "Offload", "Monitor")

---

**Conclusão:** UI agora é **clara, intuitiva e sem ambiguidades**. O usuário não tem dúvida sobre o que cada opção faz.
