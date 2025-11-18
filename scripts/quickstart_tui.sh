#!/bin/bash
# ------------------------------------------------------------
# quickstart_tui.sh — TUI Panel with Progress Bars (Ketter 3.0)
# ------------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$REPO_ROOT/dku/.venv"

# ------------------------------------------------------------
# VISUAL HELPERS
# ------------------------------------------------------------
title() {
  clear
  echo "===================================================="
  echo " KETTER 3.0 — QUICKSTART TUI PANEL (Progress Bars)"
  echo "===================================================="
  echo
}

bar() {
  local progress=$1
  local total=40
  local filled=$(( progress * total / 100 ))
  local empty=$(( total - filled ))
  printf "["
  printf "%0.s#" $(seq 1 $filled)
  printf "%0.s-" $(seq 1 $empty)
  printf "] %3d%%" "$progress"
}

task_with_bar() {
  local message="$1"
  local command="$2"

  echo
  echo "$message"
  for i in 5 20 35 60 80; do
    bar "$i"
    printf "\r"
    sleep 0.15
  done

  # Run actual command
  if bash -c "$command"; then
    bar 100
    echo "  OK"
  else
    bar 100
    echo "  FAILED"
    return 1
  fi
  echo
}

pause() {
  echo
  read -p "Pressione Enter para continuar..." _
}

# ------------------------------------------------------------
# TASKS
# ------------------------------------------------------------
run_rollback() {
  task_with_bar \
    "Executando rollback total..." \
    "bash '$REPO_ROOT/scripts/rollback_ketter_mac_v4.sh' || true"
}

run_dku() {
  task_with_bar \
    "Executando DKU pipeline..." \
    "bash '$REPO_ROOT/dku_run.sh'"
}

run_backend() {
  task_with_bar \
    'Iniciando backend...' \
    "
    if [[ ! -f '$VENV_PATH/bin/activate' ]]; then exit 1; fi;
    source '$VENV_PATH/bin/activate';
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    "
  echo "Backend disponível em http://localhost:8000"
}

run_frontend() {
  task_with_bar \
    "Iniciando frontend..." \
    "
    cd '$REPO_ROOT/frontend' || exit 1;
    npm install;
    npm run dev &
    "
  echo "Frontend disponível em http://localhost:5173"
}

# ------------------------------------------------------------
# MENU LOOP
# ------------------------------------------------------------
while true; do
  title
  echo "Selecione a operação:"
  echo
  echo " 1) Rollback total (limpa tudo)"
  echo " 2) DKU — Instalação completa"
  echo " 3) Inicializar Backend"
  echo " 4) Inicializar Frontend"
  echo " 5) Ambiente DEV (rollback + DKU + backend + frontend)"
  echo " 6) Ambiente FULL (rollback + DKU + backend + frontend)"
  echo " 7) Sair"
  echo
  read -p "Opção: " opt
  echo

  case "$opt" in
    1)
      run_rollback
      pause
      ;;
    2)
      run_dku
      pause
      ;;
    3)
      run_backend
      pause
      ;;
    4)
      run_frontend
      pause
      ;;
    5)
      run_rollback
      run_dku
      run_backend
      run_frontend
      pause
      ;;
    6)
      run_rollback
      run_dku
      run_backend
      run_frontend
      pause
      ;;
    7)
      echo "Saindo..."
      exit 0
      ;;
    *)
      echo "Opção inválida."
      pause
      ;;
  esac
done

