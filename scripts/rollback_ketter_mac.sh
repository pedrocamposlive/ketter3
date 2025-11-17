#!/bin/bash
# ------------------------------------------------------------
# KETTER 3.0 - ROLLBACK TOTAL (macOS Apple Silicon)
# ------------------------------------------------------------
# Remove PostgreSQL, Redis, venv, env vars, LaunchAgents,
# processos ativos e qualquer resíduo do ambiente anterior.
# ------------------------------------------------------------

set -e

header() {
  echo
  echo "===================================================="
  echo "$1"
  echo "===================================================="
}

# ----------------------------------------
# 0. Segurança
# ----------------------------------------
header "0. Validação inicial"
echo "Este script irá remover TODO o ambiente do Ketter no seu macOS."
echo "Continuar? (y/n)"
read -r ANS
if [[ "$ANS" != "y" ]]; then
  echo "Abortado."
  exit 1
fi

# ----------------------------------------
# 1. Parar PostgreSQL
# ----------------------------------------
header "1. Parando PostgreSQL 16"

brew services stop postgresql@16 2>/dev/null || true

launchctl remove ~/Library/LaunchAgents/homebrew.mxcl.postgresql@16 \
  2>/dev/null || true

rm -f ~/Library/LaunchAgents/homebrew.mxcl.postgresql@16.plist || true

# ----------------------------------------
# 2. Remover PostgreSQL e cluster
# ----------------------------------------
header "2. Removendo PostgreSQL & data directory"

brew uninstall --force postgresql@16 2>/dev/null || true

echo "Apagando diretório de dados..."
rm -rf /opt/homebrew/var/postgresql@16 2>/dev/null || true

# ----------------------------------------
# 3. Limpar roles e bases (se o Postgres anterior ainda estiver rodando)
# ----------------------------------------
header "3. Removendo roles e bancos do Postgres"

echo "Tentando remover role ketter_user..."
psql postgres -c "DROP ROLE IF EXISTS ketter_user;" \
  >/dev/null 2>&1 || true

echo "Tentando remover database ketter_db..."
psql postgres -c "DROP DATABASE IF EXISTS ketter_db;" \
  >/dev/null 2>&1 || true

# ----------------------------------------
# 4. Parar e remover Redis
# ----------------------------------------
header "4. Removendo Redis"

brew services stop redis 2>/dev/null || true
brew uninstall --force redis 2>/dev/null || true

rm -rf /opt/homebrew/var/redis 2>/dev/null || true

# ----------------------------------------
# 5. Matar processos em portas sensíveis (5432 / 6379)
# ----------------------------------------
header "5. Matando processos residuais"

kill_port() {
  PORT=$1
  PIDS=$(lsof -t -i :$PORT || true)
  if [ -n "$PIDS" ]; then
    echo "Matando processos na porta $PORT..."
    kill -9 $PIDS 2>/dev/null || true
  else
    echo "Nenhum processo ativo na porta $PORT."
  fi
}

kill_port 5432
kill_port 6379

# ----------------------------------------
# 6. Remover ambiente Python
# ----------------------------------------
header "6. Removendo ambiente Python (.venv)"

rm -rf .venv 2>/dev/null || true

# Pacotes instalados pelo bootstrap
header "6.1 Removendo pacotes Python instalados"
pip uninstall -y psycopg2 psycopg2-binary redis rq uvicorn alembic >/dev/null 2>&1 || true

# ----------------------------------------
# 7. Remover arquivos do projeto
# ----------------------------------------
header "7. Limpando arquivos gerados pelo Ketter"

rm -f .env 2>/dev/null || true
rm -f .env.local 2>/dev/null || true

rm -rf logs 2>/dev/null || true

rm -rf alembic/versions/* 2>/dev/null || true

# ----------------------------------------
# 8. Remover LaunchAgents residuais
# ----------------------------------------
header "8. Limpando LaunchAgents residuais"

LAUNCHD="$HOME/Library/LaunchAgents"

rm -f "$LAUNCHD/homebrew.mxcl.redis.plist" 2>/dev/null || true
rm -f "$LAUNCHD/homebrew.mxcl.postgresql@16.plist" 2>/dev/null || true

# ----------------------------------------
# 9. Validar portas novamente
# ----------------------------------------
header "9. Validando portas"

lsof -i :5432 || echo "5432 livre."
lsof -i :6379 || echo "6379 livre."

# ----------------------------------------
# 10. Resultado final
# ----------------------------------------
header " ROLLBACK CONCLUÍDO COM SUCESSO"

echo "Seu ambiente está limpo."
echo "Agora você pode rodar o bootstrap novamente em um ambiente 100% zerado."
echo
echo "Sugestão:"
echo "  scripts/bootstrap_ketter_mac.sh"
echo
echo "Fim."

