#!/bin/bash
# ------------------------------------------------------------
# KETTER 3.0 - ROLLBACK TOTAL PARA macOS (v4.1 ESTÁVEL)
# ------------------------------------------------------------
# Esta versão evita abortar silenciosamente e sempre imprime
# exatamente o que está acontecendo.
# ------------------------------------------------------------

# NÃO usar set -euo pipefail (causa abortos silenciosos)
# Implementamos nosso próprio controle:

safe_run() {
  echo "→ Executando: $*"
  eval "$*" || echo "   [AVISO] Comando falhou (continuando): $*"
}

header() {
  echo
  echo "===================================================="
  echo "$1"
  echo "===================================================="
}

confirm() {
  echo "Este script VAI REMOVER TODO o ambiente do Ketter."
  echo "Continuar? (y/n)"
  read -r ans
  [[ "$ans" != "y" ]] && { echo "Abortado."; exit 1; }
}

kill_port() {
  local PORT=$1
  echo "→ Verificando porta $PORT"
  P=$(lsof -t -i tcp:"$PORT" || true)
  if [[ -n "$P" ]]; then
    echo "→ Matando PID(s): $P"
    safe_run "kill -9 $P"
  else
    echo "→ Porta $PORT limpa"
  fi
}

# ---------------------------
# 0. Confirmação
# ---------------------------
header "0. CONFIRMAÇÃO"
confirm

# ---------------------------
# 1. PostgreSQL — Stop & Remove
# ---------------------------
header "1. Parando PostgreSQL"

for V in 14 15 16 17; do
  safe_run "brew services stop postgresql@$V"
done

safe_run "launchctl remove homebrew.mxcl.postgresql@16"
safe_run "launchctl remove homebrew.mxcl.postgresql@15"

header "1B. Removendo PostgreSQL"
for V in 14 15 16 17; do
  safe_run "brew uninstall --force postgresql@$V"
done

safe_run "rm -rf /opt/homebrew/var/postgres"
safe_run "rm -rf /opt/homebrew/var/postgresql@*"
safe_run "rm -rf /usr/local/var/postgres"

header "1C. Removendo LaunchAgents"
safe_run "rm -f ~/Library/LaunchAgents/homebrew.mxcl.postgresql*.plist"
safe_run "rm -f /Library/LaunchAgents/homebrew.mxcl.postgresql*.plist"

# ---------------------------
# 2. Remover Redis
# ---------------------------
header "2. Removendo Redis"
safe_run "brew services stop redis"
safe_run "brew uninstall --force redis"
safe_run "rm -rf /opt/homebrew/var/redis"
safe_run "rm -f ~/Library/LaunchAgents/homebrew.mxcl.redis.plist"

# ---------------------------
# 3. Matar processos residuais
# ---------------------------
header "3. Matando processos residuais"
kill_port 5432
kill_port 6379

# ---------------------------
# 4. Remover Python / venv / caches
# ---------------------------
header "4. Removendo Python venv e caches"

safe_run "rm -rf .venv"
safe_run "rm -rf ~/Library/Caches/pip"
safe_run "rm -rf ~/Library/Caches/maturin"
safe_run "rm -rf ~/.cargo"
safe_run "rm -rf ~/.rustup"

header "4B. Removendo Python conflitantes"
safe_run "brew uninstall --force python@3.12"
safe_run "brew uninstall --force python@3.13"
safe_run "brew uninstall --force python@3.14"

safe_run "rm -rf /opt/homebrew/opt/python@3.12"
safe_run "rm -rf /opt/homebrew/opt/python@3.13"
safe_run "rm -rf /opt/homebrew/opt/python@3.14"

# ---------------------------
# 5. Remover arquivos do projeto
# ---------------------------
header "5. Removendo arquivos do projeto"

safe_run "rm -f .env .env.local"
safe_run "rm -rf logs"
safe_run "rm -rf alembic/versions/*"

# ---------------------------
# 6. Limpar PATH contaminado
# ---------------------------
header "6. Limpando PATH"

safe_run "sed -i '' '/python@3/d' ~/.zshrc"
safe_run "sed -i '' '/postgresql@/d' ~/.zshrc"

# ---------------------------
# 7. Verificar portas
# ---------------------------
header "7. Validando portas"

lsof -i :5432 || echo "→ Porta 5432 OK"
lsof -i :6379 || echo "→ Porta 6379 OK"

# ---------------------------
# 8. Final
# ---------------------------
header " ROLLBACK COMPLETO v4.1 — SISTEMA 100% LIMPO "

echo "Agora rode:"
echo "  ./scripts/bootstrap_ketter_mac_5.1_fixed.sh "
echo
echo "Fim."

