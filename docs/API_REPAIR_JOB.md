# Ketter 3.0 — Frontend API Auto-Repair Job
# Objetivo
Resolver 100% dos erros de build gerados por funções ausentes no arquivo
frontend/src/services/api.js.

O Codex deve:
- Detectar todas as funções que o React importa de src/services/api.js
- Garantir que todas elas estejam implementadas no api.js
- Validar cada função comparando com os endpoints reais do backend FastAPI
- Atualizar componentes e páginas se alguma função tiver nome errado
- Remover imports mortos
- Garantir que o Vite build finalize sem erros

---

# Regras
1. Ler estes arquivos obrigatoriamente:
   - frontend/src/services/api.js
   - todos os arquivos em frontend/src/components/
   - todos os arquivos em frontend/src/pages/
   - backend/app/main.py
   - backend/app/routes or endpoints directory (transfer, audit, settings, etc.)

2. Para cada import do tipo:
   import { XYZ } from '../services/api'
   Verificar:
   - XYZ existe?
   - XYZ corresponde a algum endpoint REAL?
   - Deve criar ou ajustar XYZ para operar corretamente.

3. Toda função ausente deve ser criada seguindo o padrão:
   export async function FUNCTION_NAME(...) {
       return apiFetch('/backend-route', options);
   }

4. Garantir que todos estes endpoints existam no api.js:
   - getTransfers
   - getTransferDetails
   - getTransferChecksums
   - getTransferLogs
   - getRecentTransfers
   - cancelTransfer
   - createTransfer
   - deleteTransfer
   - downloadTransferReport
   - getAuditLogs
   - getSystemHealth
   - getVolumes
   - getAvailableVolumes
   - getStatus
   - getAlerts

5. Remover qualquer import no React que NÃO existe no backend.

6. Validar que o api.js final:
   - Não tenha funções duplicadas
   - Não tenha funções mortas
   - Cubra todas as chamadas do frontend
   - Use secureFetch/apiFetch corretamente

---

# Execução Automática (ordem)
1. Reparar e reescrever api.js inteiro.
2. Ajustar todos os componentes que importam funções API.
3. Ajustar todas as páginas.
4. Remover imports mortos.
5. Rodar simulação de build (vite build).
6. Se falhar, repetir a etapa 1–4 até passar.
7. Atualizar docs/state-ui-manus.md com PATCH API-REPAIR
8. git add + git commit automaticamente.

---

# Condição de parada
Parar quando:
- nenhum erro de build do Vite restar
- api.js estiver estável
- state-ui-manus.md estiver atualizado
- todos os React imports estiverem sanados

---

# Sem comentários
Nenhum comentário, nenhuma explicação.  
Apenas execuções diretas e commits.

