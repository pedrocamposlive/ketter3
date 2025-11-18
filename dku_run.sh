#!/bin/bash
# ------------------------------------------------------------
# KETTER 3.0 — DKU MAIN RUNNER (v10)
# ------------------------------------------------------------

set -euo pipefail
IFS=$'\n\t'

# ------------------------------------------------------------
# Path detection (robusto para ser chamado de qualquer lugar)
# ------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_ROOT="${REPO_ROOT}/dku"

LOG_DIR="${SCRIPT_ROOT}/docs/dku_reports"
mkdir -p "$LOG_DIR"

RUN_LOG="${LOG_DIR}/dku_run_$(date '+%Y%m%d_%H%M%S').log"
echo "[DKU-RUN] DKU Run initiated with log file at $RUN_LOG" | tee -a "$RUN_LOG"

# ------------------------------------------------------------
# Função de execução de módulos
# ------------------------------------------------------------
run_module() {
    local module_name="$1"
    local script_path="$2"

    echo "[DKU-RUN] Starting module $module_name." | tee -a "$RUN_LOG"

    # Verifica se o script existe antes de rodar
    if [[ ! -f "$script_path" ]]; then
        echo "[DKU-RUN] ERROR: Module script not found: $script_path" | tee -a "$RUN_LOG"
        exit 1
    fi

    # Executa o módulo
    if ! bash "$script_path" >> "$RUN_LOG" 2>&1; then
        echo "[DKU-RUN] Module $module_name failed. Triggering rollback." | tee -a "$RUN_LOG"

        # rollback específico, se existir
        local rollback_script="${SCRIPT_ROOT}/rollback/rollback_${module_name}.sh"
        if [[ -f "$rollback_script" ]]; then
            echo "[DKU-RUN] Running rollback script for module $module_name." | tee -a "$RUN_LOG"
            bash "$rollback_script" >> "$RUN_LOG" 2>&1 || true
        else
            echo "[DKU-RUN] No rollback script found for $module_name." | tee -a "$RUN_LOG"
        fi

        exit 1
    fi

    echo "[DKU-RUN] Module $module_name completed." | tee -a "$RUN_LOG"
}

# ------------------------------------------------------------
# Execução de todos os módulos (pipeline DKU)
# ------------------------------------------------------------
run_module "00" "$SCRIPT_ROOT/00_hardware_validation.sh"
run_module "01" "$SCRIPT_ROOT/01_system_prep.sh"
run_module "02" "$SCRIPT_ROOT/02_install_dependencies.sh"
run_module "03_python" "$SCRIPT_ROOT/03_python_setup.sh"
run_module "03b_redis" "$SCRIPT_ROOT/03b_redis_setup.sh"
run_module "04" "$SCRIPT_ROOT/04_post_install_validation.sh"
run_module "05" "$SCRIPT_ROOT/05_generate_report.sh"

echo "[DKU-RUN] DKU Run completed successfully." | tee -a "$RUN_LOG"
exit 0
