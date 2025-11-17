#!/bin/bash
# ------------------------------------------------------------
# KETTER 3.0 - BOOTSTRAP macOS (Apple Silicon) - Versão 5.1
# Foco: ambiente determinístico usando Homebrew + PostgreSQL 16
# ------------------------------------------------------------

set -euo pipefail
set -o errtrace
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

PG_VERSION="16"
PG_FORMULA="postgresql@${PG_VERSION}"
PG_PREFIX="/opt/homebrew/opt/${PG_FORMULA}"
PG_DATA_DIR="/opt/homebrew/var/${PG_FORMULA}"
PG_BIN="${PG_PREFIX}/bin"
PATH="${PG_BIN}:${PATH}"
export PATH

DEFAULT_PG_SUPERUSER="${USER}"
KETTER_DB="ketter"
KETTER_USER="ketter_user"
KETTER_USER_PASS="ketter_user_pass"
KETTER_ADMIN="ketter_admin"
KETTER_ADMIN_PASS="ketter_admin_pass"

PY_FORMULA="python@3.11"
PY_BIN="/opt/homebrew/opt/${PY_FORMULA}/bin/python3.11"
VENV_PATH="${REPO_ROOT}/.venv"

REDIS_FORMULA="redis"
REDIS_PORT="6379"

ENV_FILE="${REPO_ROOT}/.env"
ROLLBACK_SCRIPT="${REPO_ROOT}/scripts/rollback_ketter_mac_v4.sh"

UVICORN_PORT="9001"
UVICORN_HOST="127.0.0.1"
UVICORN_LOG="${REPO_ROOT}/.bootstrap_uvicorn.log"

log_step() {
  echo
  echo "===================================================="
  echo "[STEP] $1"
  echo "===================================================="
}

log_info() { echo "[INFO] $1"; }
log_warn() { echo "[WARN] $1"; }
log_error() { echo "[ERROR] $1" >&2; }

handle_failure() {
  local exit_code="${1:-1}"
  local line="${2:-0}"
  log_error "Falha detectada (linha ${line}). Executando rollback seguro."
  if [[ -x "$ROLLBACK_SCRIPT" ]]; then
    if ! "$ROLLBACK_SCRIPT"; then
      log_warn "Rollback retornou erro. Verifique manualmente."
    fi
  else
    log_warn "Script de rollback não encontrado em ${ROLLBACK_SCRIPT}."
  fi
  exit "$exit_code"
}
trap 'handle_failure $? $LINENO' ERR

require_command() {
  local cmd="$1"
  local pkg="$2"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log_error "Comando '${cmd}' não encontrado. Instale ${pkg} e tente novamente."
    exit 1
  fi
}

ensure_homebrew() {
  log_step "Verificando Homebrew"
  if ! command -v brew >/dev/null 2>&1; then
    log_info "Homebrew não encontrado. Instalando..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  else
    log_info "Atualizando fórmulas do Homebrew..."
    brew update
  fi
}

ensure_formula_installed() {
  local formula="$1"
  if ! brew list --versions "$formula" >/dev/null 2>&1; then
    log_info "Instalando ${formula}..."
    brew install "$formula"
  else
    log_info "${formula} já instalado."
  fi
}

reinitialize_pg_cluster() {
  log_warn "Recriando cluster do PostgreSQL em ${PG_DATA_DIR}"
  brew services stop "$PG_FORMULA" >/dev/null 2>&1 || true
  rm -rf "$PG_DATA_DIR"
  mkdir -p "$PG_DATA_DIR"
  "${PG_BIN}/initdb" --locale="C" --encoding="UTF8" -D "$PG_DATA_DIR"
}

ensure_pg_cluster() {
  log_step "Garantindo cluster PostgreSQL ${PG_VERSION}"
  ensure_formula_installed "$PG_FORMULA"
  if [[ ! -d "$PG_DATA_DIR" ]] || [[ ! -f "$PG_DATA_DIR/PG_VERSION" ]]; then
    reinitialize_pg_cluster
  else
    if ! "${PG_BIN}/pg_controldata" "$PG_DATA_DIR" >/dev/null 2>&1; then
      log_warn "Cluster aparentemente corrompido. Recriando..."
      reinitialize_pg_cluster
    else
      log_info "Cluster existente validado."
    fi
  fi
  log_info "Iniciando serviço PostgreSQL..."
  brew services start "$PG_FORMULA" >/dev/null 2>&1 || brew services restart "$PG_FORMULA"
}

wait_for_postgres() {
  log_info "Aguardando PostgreSQL responder..."
  local attempts=30
  until "${PG_BIN}/pg_isready" -q >/dev/null 2>&1; do
    if (( attempts == 0 )); then
      log_error "PostgreSQL não respondeu após várias tentativas."
      exit 1
    fi
    attempts=$((attempts - 1))
    sleep 2
  done
  log_info "PostgreSQL operacional."
}

psql_super() {
  "${PG_BIN}/psql" --username="$DEFAULT_PG_SUPERUSER" --dbname="postgres" -v ON_ERROR_STOP=1 "$@"
}

psql_admin() {
  PGPASSWORD="$KETTER_ADMIN_PASS" "${PG_BIN}/psql" --username="$KETTER_ADMIN" --dbname="postgres" -v ON_ERROR_STOP=1 "$@"
}

ensure_db_roles_and_database() {
  log_step "Configurando roles e banco do PostgreSQL"

  if ! psql_super -c '\q' >/dev/null 2>&1; then
    log_error "Não foi possível autenticar como usuário local ${DEFAULT_PG_SUPERUSER}."
    exit 1
  fi

  log_info "Criando/atualizando role ${KETTER_ADMIN} (superuser garantido)."
  psql_super <<SQL
DO \$\$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${KETTER_ADMIN}') THEN
    EXECUTE format('ALTER ROLE %I WITH LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD %L', '${KETTER_ADMIN}', '${KETTER_ADMIN_PASS}');
  ELSE
    EXECUTE format('CREATE ROLE %I WITH LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD %L', '${KETTER_ADMIN}', '${KETTER_ADMIN_PASS}');
  END IF;
END
\$\$;
SQL

  log_info "Criando/atualizando role ${KETTER_USER} (LOGIN, CREATEDB)."
  psql_admin <<SQL
DO \$\$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${KETTER_USER}') THEN
    EXECUTE format('ALTER ROLE %I WITH LOGIN CREATEDB PASSWORD %L', '${KETTER_USER}', '${KETTER_USER_PASS}');
  ELSE
    EXECUTE format('CREATE ROLE %I WITH LOGIN CREATEDB PASSWORD %L', '${KETTER_USER}', '${KETTER_USER_PASS}');
  END IF;
END
\$\$;
SQL

  log_info "Garantindo database ${KETTER_DB} com owner ${KETTER_USER}."
  local exists
  exists="$(psql_admin -Atc "SELECT 1 FROM pg_database WHERE datname='${KETTER_DB}'" || true)"
  if [[ "$exists" != "1" ]]; then
    psql_admin -c "CREATE DATABASE ${KETTER_DB} OWNER ${KETTER_USER};"
  else
    psql_admin -c "ALTER DATABASE ${KETTER_DB} OWNER TO ${KETTER_USER};"
  fi
}

ensure_python_env() {
  log_step "Configurando Python 3.11 e virtualenv"
  ensure_formula_installed "$PY_FORMULA"
  if [[ ! -x "$PY_BIN" ]]; then
    log_error "Python 3.11 não encontrado em ${PY_BIN}"
    exit 1
  fi
  if [[ -d "$VENV_PATH" ]]; then
    log_info "Removendo venv anterior para garantir determinismo."
    rm -rf "$VENV_PATH"
  fi
  log_info "Criando nova venv em ${VENV_PATH}"
  "$PY_BIN" -m venv "$VENV_PATH"
  # shellcheck disable=SC1090
  source "${VENV_PATH}/bin/activate"
  log_info "Instalando dependências Python..."
  pip install --upgrade pip wheel setuptools
  pip install -r "${REPO_ROOT}/requirements.txt"
}

ensure_redis() {
  log_step "Instalando e validando Redis"
  ensure_formula_installed "$REDIS_FORMULA"
  log_info "Iniciando serviço Redis..."
  brew services start "$REDIS_FORMULA" >/dev/null 2>&1 || brew services restart "$REDIS_FORMULA"
  require_command "nc" "netcat"
  local attempts=15
  until nc -z "$UVICORN_HOST" "$REDIS_PORT" >/dev/null 2>&1; do
    if (( attempts == 0 )); then
      log_error "Redis não respondeu na porta ${REDIS_PORT}."
      exit 1
    fi
    attempts=$((attempts - 1))
    sleep 1
  done
  log_info "Redis operacional."
}

generate_env_file() {
  log_step "Gerando arquivo .env determinístico"
  cat > "$ENV_FILE" <<EOF
DATABASE_URL=postgresql+psycopg2://${KETTER_USER}:${KETTER_USER_PASS}@127.0.0.1:5432/${KETTER_DB}
DATABASE_ADMIN_URL=postgresql+psycopg2://${KETTER_ADMIN}:${KETTER_ADMIN_PASS}@127.0.0.1:5432/${KETTER_DB}
REDIS_URL=redis://127.0.0.1:${REDIS_PORT}/0
EOF
  chmod 600 "$ENV_FILE"
  log_info ".env criado em ${ENV_FILE}"
}

run_alembic() {
  log_step "Executando migrações Alembic"
  alembic upgrade head
}

run_uvicorn_sanity() {
  log_step "Teste final com Uvicorn"
  : > "$UVICORN_LOG"
  local uvicorn_cmd=("uvicorn" "app.main:app" "--host" "$UVICORN_HOST" "--port" "$UVICORN_PORT")
  "${uvicorn_cmd[@]}" >"$UVICORN_LOG" 2>&1 &
  local uvicorn_pid=$!
  local attempts=20
  local healthy="false"
  until (( attempts == 0 )); do
    if nc -z "$UVICORN_HOST" "$UVICORN_PORT" >/dev/null 2>&1; then
      healthy="true"
      break
    fi
    attempts=$((attempts - 1))
    sleep 1
  done
  if [[ "$healthy" != "true" ]]; then
    log_error "Uvicorn não respondeu. Consulte ${UVICORN_LOG}."
    kill "$uvicorn_pid" >/dev/null 2>&1 || true
    wait "$uvicorn_pid" >/dev/null 2>&1 || true
    exit 1
  fi
  log_info "Uvicorn respondeu corretamente. Encerrando processo..."
  kill "$uvicorn_pid" >/dev/null 2>&1 || true
  wait "$uvicorn_pid" >/dev/null 2>&1 || true
}

confirm_execution() {
  log_step "Confirmação do usuário"
  echo "Este script irá configurar COMPLETAMENTE o ambiente do Ketter."
  read -rp "Continuar? (y/n) " ans
  if [[ "$ans" != "y" ]]; then
    log_warn "Bootstrap cancelado pelo usuário."
    exit 1
  fi
}

main() {
  confirm_execution
  ensure_homebrew
  ensure_pg_cluster
  wait_for_postgres
  ensure_db_roles_and_database
  ensure_redis
  ensure_python_env
  generate_env_file
  run_alembic
  run_uvicorn_sanity

  log_step "Bootstrap concluído com sucesso"
  echo "Ambiente pronto."
  echo "Ative o venv com: source .venv/bin/activate"
  echo "Banco de dados disponível em ${KETTER_DB} (user ${KETTER_USER})."
}

main "$@"
