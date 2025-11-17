#!/usr/bin/env bash
set -euo pipefail

header() {
  echo "===================================================="
  echo "$1"
  echo "===================================================="
}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

REDIS_URL="redis://localhost:6379/0"
PG_VERSION=16
PG_SERVICE="postgresql@${PG_VERSION}"
PG_HOST="127.0.0.1"
PG_PORT="5432"
PG_SUPERUSER="${PG_SUPERUSER:-$USER}"
DB_NAME="ketter"
DB_USER="ketter_user"
DB_PASSWORD="$(openssl rand -hex 16)"
ENV_FILE=".env"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
PSQL_COMMON=(-h "$PG_HOST" -p "$PG_PORT" -U "$PG_SUPERUSER" -v ON_ERROR_STOP=1)

cd "$PROJECT_ROOT"

echo "Script localizado em: $SCRIPT_DIR"
echo "Raiz do projeto detectada em: $PROJECT_ROOT"
echo "Mudando para a raiz..."

wait_for_postgres() {
  local retries=${1:-60}
  local counter=0
  echo "Aguardando PostgreSQL iniciar..."
  until pg_isready -h "$PG_HOST" -p "$PG_PORT" >/dev/null 2>&1; do
    sleep 1
    counter=$((counter + 1))
    if (( counter >= retries )); then
      echo "PostgreSQL não respondeu após ${retries}s."
      exit 1
    fi
  done
  echo "Postgres está pronto."
}

psql_exec() {
  local sql="$1"
  local db="${2:-postgres}"
  psql "${PSQL_COMMON[@]}" -d "$db" -c "$sql"
}

psql_query() {
  local sql="$1"
  local db="${2:-postgres}"
  psql "${PSQL_COMMON[@]}" -d "$db" -At -c "$sql"
}

header "1. Verificando Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew não encontrado. Instalando..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  brew update
fi

header "2. Instalando PostgreSQL ${PG_VERSION}"
brew services stop "$PG_SERVICE" >/dev/null 2>&1 || true
brew install "$PG_SERVICE"
brew services start "$PG_SERVICE"
wait_for_postgres 60

header "2A. Garantindo role postgres"
if [[ "$(psql_query "SELECT 1 FROM pg_roles WHERE rolname='postgres';")" != "1" ]]; then
  psql_exec "CREATE ROLE \"postgres\" WITH LOGIN SUPERUSER CREATEDB;"
else
  echo "Role postgres já existe."
fi

header "2B. Configurando ${DB_USER}"
if [[ "$(psql_query "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER';")" == "1" ]]; then
  echo "Atualizando senha de ${DB_USER}."
  psql_exec "ALTER ROLE \"$DB_USER\" WITH LOGIN PASSWORD '$DB_PASSWORD' CREATEDB;"
else
  echo "Criando role ${DB_USER}."
  psql_exec "CREATE ROLE \"$DB_USER\" WITH LOGIN PASSWORD '$DB_PASSWORD' CREATEDB;"
fi

header "2C. Criando banco ${DB_NAME}"
if [[ "$(psql_query "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';")" == "1" ]]; then
  echo "${DB_NAME} já existe; ajustando proprietário e permissões."
  psql_exec "ALTER DATABASE \"$DB_NAME\" OWNER TO \"$DB_USER\";"
else
  createdb -h "$PG_HOST" -p "$PG_PORT" -U "$PG_SUPERUSER" -O "$DB_USER" "$DB_NAME"
fi
psql_exec "GRANT ALL PRIVILEGES ON DATABASE \"$DB_NAME\" TO \"$DB_USER\";"

header "3. Instalando Redis"
brew install redis
if ! brew services restart redis >/dev/null 2>&1; then
  brew services start redis
fi

header "4. Preparando ambiente Python"
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 não encontrado no PATH."
  exit 1
fi
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python3 -m pip install --upgrade pip wheel setuptools
if [ -f "$REQUIREMENTS_FILE" ]; then
  python3 -m pip install -r "$REQUIREMENTS_FILE"
else
  echo "ERRO: requirements.txt não encontrado em $PROJECT_ROOT"
  exit 1
fi

header "5. Criando .env"
if [ -f "$ENV_FILE" ]; then
  backup="${ENV_FILE}.bootstrap.bak.$(date +%Y%m%d%H%M%S)"
  cp "$ENV_FILE" "$backup"
  echo "Backup do .env salvo em $backup"
fi
DATABASE_URL="postgresql+psycopg2://$DB_USER:$DB_PASSWORD@localhost:$PG_PORT/$DB_NAME"
SECRET_KEY="$(openssl rand -hex 32)"
cat <<ENVEOF > "$ENV_FILE"
DATABASE_URL=$DATABASE_URL
REDIS_URL=$REDIS_URL
APP_ENV=development
ENVIRONMENT=development
LOG_LEVEL=INFO
SECRET_KEY=$SECRET_KEY
ENVEOF
export DATABASE_URL
export REDIS_URL

header "6. Executando migrações Alembic"
if [ ! -f "alembic.ini" ]; then
  echo "ERRO: alembic.ini não encontrado em $PROJECT_ROOT"
  exit 1
fi
if ! command -v alembic >/dev/null 2>&1; then
  echo "ERRO: alembic não está disponível na .venv"
  exit 1
fi
alembic upgrade head

header "Ketter instalado com sucesso!"
echo "Para rodar o backend:"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Para rodar o worker:"
echo "  source .venv/bin/activate"
echo "  rq worker --url redis://localhost:6379/0 default"
echo ""
