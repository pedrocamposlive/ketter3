UI_DEV_SERVER_FIX.md
Objetivo

Restaurar o Vite Dev Server do frontend (npm run dev), garantir que ele esteja rodando corretamente na porta 5173 e impedir que o FastAPI seja servido no lugar da UI.

O Codex deve:

verificar o problema,

corrigir a configuração,

reescrever arquivos necessários,

testar novamente,

confirmar que o frontend está servindo a UI.

1. Diagnóstico automático

O Codex deve identificar por que o Vite não aparece ao acessar http://localhost:5173.

Executar:

Verificar se o Vite está realmente rodando:

npm run dev -- --debug


Checar portas:

lsof -i :5173
lsof -i :3001
lsof -i :5050


Se a porta 5173 não estiver ocupada pelo Vite, continuar.

2. Reparo obrigatório

O Codex deve aplicar estes reparos automaticamente:

2.1 Corrigir vite.config.js

Arquivo: frontend/vite.config.js

O conteúdo deve ser reescrito exatamente assim:

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    host: "localhost"
  }
});

2.2 Garantir que existe package.json correto

Arquivo: frontend/package.json

O Codex deve remover qualquer linha:

"proxy": "http://localhost:3001"


ou equivalentes.

2.3 Garantir que não existe conflito com FastAPI

Verificar se não existe nenhum vite.config.js duplicado.
Regras obrigatórias:

Ele deve existir somente em frontend/vite.config.js

Não pode existir um config dentro da raiz do repo

Não pode existir config dentro de /src

2.4 Remover cache do Vite

Executar:

rm -rf node_modules/.vite
rm -rf node_modules
npm install

3. Teste automatizado

O Codex deve rodar:

npm run dev -- --port=5050 --debug


Testar:

/@vite/client deve responder

A porta deve estar registrada:

lsof -i :5050

4. Se falhar novamente → realizar fallback agressivo

O Codex deve:

Recriar o diretório frontend/node_modules

Reinstalar dependências

Reescrever completamente vite.config.js

Garantir que nenhum processo do backend esteja sendo servido via proxy

Reinstalar:

npm install

5. Confirmação

O Codex deve validar:

Vite está rodando e escutando em 5173 ou 5050

/@vite/client responde no navegador

Não aparece mais a resposta JSON do backend

Se tudo OK → parar.

6. Regras para execução

Não gerar comentários.

Não gerar explicações.

Apenas ações diretas.

Processar este arquivo como fonte da verdade.

Após resolver, parar imediatamente.
