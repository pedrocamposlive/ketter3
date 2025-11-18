#!/bin/bash
# ------------------------------------------------------------
# KETTER 3.0 — CHECKLIST AUTOMATIZADO PÓS-INSTALAÇÃO (macOS)
# ------------------------------------------------------------
# Este script executa verificações automáticas após o bootstrap:
# - Verificar serviços: PostgreSQL, Redis
# - Validar backend: health-check, portas
# - Validar worker RQ
# - Validar frontend em modo dev
# - Gerar relatório final
# ------------------------------------------------------------

set -euo pipefail

REPORT="ketter_post_install_report_$(date '+%Y%m%d_%H%M%S').txt"

header() {
  echo "====================================================" | tee -a "$REPORT"
  echo "$1" | tee -a "$REPORT"
  echo "====================================================" | tee -a "$REPORT"
}

check_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "FALHA: comando '$1' não encontrado" | tee -a "$REPORT"
    exit 1
  fi
}

header "1. Verificando comandos essenciais"
check_command python3
check_command psql
check_command redis-cli
check_command lsof
check_command curl

header "2. Verificando serviços (PostgreSQL e Redis)"

echo "PostgreSQL:" | tee -a "$REPORT"
pg_isready 2>&1 | tee -a "$REPORT"

echo "Redis:" | tee -a "$REPORT"
redis-cli ping 2>&1 | tee -a "$REPORT"

header "3. Checando portas esperadas"

echo "Porta 5432 (Postgres):" | tee -a "$REPORT"
lsof -i tcp:5432 || true | tee -a "$REPORT"

echo "Porta 6379 (Redis):" | tee -a "$REPORT"
lsof -i tcp:6379 || true | tee -a "$REPORT"

header "4. Testando backend (FastAPI)"

echo "Iniciando backend para teste..." | tee -a "$REPORT"
python3 -m uvicorn app.main:app --port 8000 --log-level warning &
BACK_PID=$!
sleep 3

echo "Health-check:" | tee -a "$REPORT"
curl -s http://127.0.0.1:8000/health | tee -a "$REPORT"

header "5. Testando Worker RQ"

echo "Iniciando worker temporário..." | tee -a "$REPORT"
rq worker test_queue --url redis://127.0.0.1:6379 &
WORKER_PID=$!
sleep 3

echo "Worker rodando?" | tee -a "$REPORT"
ps -p $WORKER_PID | tee -a "$REPORT"

header "6. Testando Frontend (modo dev)"

echo "Instalando dependências do frontend..." | tee -a "$REPORT"
cd frontend
npm install --silent

echo "Subindo frontend..." | tee -a "$REPORT"
npm run dev --silent &
FRONT_PID=$!
sleep 5

echo "Testando acesso ao frontend (porta 5173)..." | tee -a "$REPORT"
curl -s http://127.0.0.1:5173 | head -n 5 | tee -a "$REPORT"

cd ..

header "7. Encerrando processos temporários"
kill $BACK_PID || true
kill $WORKER_PID || true
kill $FRONT_PID || true

header "Relatório final salvo em: $REPORT"
echo "Checklist concluído."
