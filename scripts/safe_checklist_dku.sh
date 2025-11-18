#!/bin/bash
# ------------------------------------------------------------
# KETTER 3.0 — CHECKLIST DKU-SAFE (PÓS-INSTALAÇÃO)
# ------------------------------------------------------------
# Esta versão é segura para rodar dentro da pipeline DKU.
# Não inicia backend, frontend ou workers.
# Apenas valida componentes essenciais:
#  - PostgreSQL (serviço, roles, database)
#  - Redis (serviço e resposta)
#  - Python venv
#  - Configurações mínimas do projeto
#  - Estrutura de diretórios
#  - Migrações Alembic aplicadas
# ------------------------------------------------------------

set -euo pipefail

REPO_ROOT="$(pwd)"
VENV_PATH="${REPO_ROOT}/.venv"
PG_BIN="/opt/homebrew/opt/postgresql@16/bin"
PG_ISREADY="${PG_BIN}/pg_isready"
PSQL="${PG_BIN}/psql"
REPORT_DIR="${REPO_ROOT}/docs/dku_reports"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
REPORT="${REPORT_DIR}/checklist_dku_${TIMESTAMP}.txt"

mkdir -p "$REPORT_DIR"

header() {
  echo "====================================================" | tee -a "$REPORT"
  echo "$1" | tee -a "$REPORT"
  echo "====================================================" | tee -a "$REPORT"
}

# ------------------------------------------------------------
# 1. Validar virtualenv
# ------------------------------------------------------------
header "1. Verificando Python Virtualenv"

if [[ ! -d "$VENV_PATH" ]]; then
  echo "FALHA: Virtualenv não encontrado em $VENV_PATH" | tee -a "$REPORT"
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV_PATH/bin/activate"

python3 --version | tee -a "$REPORT"
pip --version | tee -a "$REPORT"

# ------------------------------------------------------------
# 2. Verificar PostgreSQL
# ------------------------------------------------------------
header "2. Validando PostgreSQL"

if [[ ! -x "$PG_ISREADY" ]]; then
  echo "FALHA: pg_isready não encontrado em $PG_ISREADY" | tee -a "$REPORT"
  exit 1
fi

echo "Status do serviço:" | tee -a "$REPORT"
"$PG_ISREADY" -h 127.0.0.1 -p 5432 | tee -a "$REPORT"

echo "Conexão com role ketter_user:" | tee -a "$REPORT"
if ! PGPASSWORD="ketter_user_pass" "$PSQL" -h 127.0.0.1 -U ketter_user -d ketter -c '\l' >> "$REPORT" 2>&1; then
  echo "FALHA: Não foi possível conectar ao banco ketter com ketter_user" | tee -a "$REPORT"
  exit 1
fi

# ------------------------------------------------------------
# 3. Verificar tabelas criadas (migrations)
# ------------------------------------------------------------
header "3. Validando Alembic / Migrations"

if ! PGPASSWORD="ketter_user_pass" "$PSQL" -h 127.0.0.1 -U ketter_user -d ketter -c '\dt' | tee -a "$REPORT"; then
  echo "FALHA: Erro listando tabelas" | tee -a "$REPORT"
  exit 1
fi

# ------------------------------------------------------------
# 4. Validar Redis
# ------------------------------------------------------------
header "4. Validando Redis"

if ! command -v redis-cli >/dev/null 2>&1; then
  echo "FALHA: redis-cli não encontrado" | tee -a "$REPORT"
  exit 1
fi

echo "Status do Redis:" | tee -a "$REPORT"
if ! redis-cli ping >> "$REPORT" 2>&1; then
  echo "FALHA: Redis não respondeu ao ping" | tee -a "$REPORT"
  exit 1
fi

# ------------------------------------------------------------
# 5. Estrutura de diretórios essenciais
# ------------------------------------------------------------
header "5. Estrutura de diretórios essenciais"

check_dir() {
  if [[ ! -d "$1" ]]; then
    echo "FALHA: diretório ausente → $1" | tee -a "$REPORT"
    exit 1
  fi
  echo "OK: $1" | tee -a "$REPORT"
}

check_dir "${REPO_ROOT}/app"
check_dir "${REPO_ROOT}/app/models"
check_dir "${REPO_ROOT}/app/schemas"
check_dir "${REPO_ROOT}/app/api"
check_dir "${REPO_ROOT}/migrations"
check_dir "${REPO_ROOT}/scripts"

# ------------------------------------------------------------
# 6. Verificar arquivo .env
# ------------------------------------------------------------
header "6. Validando arquivo .env"

if [[ ! -f "${REPO_ROOT}/.env" ]]; then
  echo "FALHA: arquivo .env não encontrado" | tee -a "$REPORT"
  exit 1
fi

grep -E "POSTGRES_HOST|POSTGRES_DB|POSTGRES_USER" "${REPO_ROOT}/.env" | tee -a "$REPORT"

# ------------------------------------------------------------
# 7. Conclusão
# ------------------------------------------------------------
header "Checklist DKU-safe concluído com sucesso."
echo "Relatório salvo em: $REPORT" | tee -a "$REPORT"


