#!/usr/bin/env bash
set -euo pipefail

API_BASE="http://localhost:8000"

header() {
  echo
  echo "===================================================="
  echo "$1"
  echo "===================================================="
}

check_api() {
  header "Checking API health"
  if curl -fsS "${API_BASE}/health" >/dev/null; then
    echo "API is healthy."
  else
    echo "ERROR: API is not responding on ${API_BASE}/health"
    exit 1
  fi
}

post_job() {
  local src="$1"
  local dst="$2"
  local mode="$3"

  echo "POST /jobs: source_path=${src}, destination_path=${dst}, mode=${mode}"
  local resp
  resp=$(curl -s -X POST "${API_BASE}/jobs" \
    -H "Content-Type: application/json" \
    -d "{
      \"source_path\": \"${src}\",
      \"destination_path\": \"${dst}\",
      \"mode\": \"${mode}\"
    }")

  echo "Raw response:"
  echo "${resp}" | jq

  local id
  id=$(echo "${resp}" | jq -r '.id')
  if [[ "${id}" == "null" || -z "${id}" ]]; then
    echo "ERROR: could not extract job id from response."
    exit 1
  fi

  echo "Job id: ${id}"
  echo "${id}"
}

wait_for_job() {
  local id="$1"
  local max_tries=60
  local i=0

  echo "Waiting for job ${id} to finish..."
  while (( i < max_tries )); do
    local status
    status=$(curl -s "${API_BASE}/jobs/${id}/detail" | jq -r '.status')

    echo "  [${i}] status=${status}"

    if [[ "${status}" != "pending" && "${status}" != "running" && "${status}" != "null" ]]; then
      echo "Job ${id} finished with status=${status}"
      return 0
    fi

    sleep 1
    ((i++))
  done

  echo "ERROR: timeout waiting for job ${id}"
  exit 1
}

print_job_summary() {
  local id="$1"
  echo
  echo "Job ${id} summary:"
  curl -s "${API_BASE}/jobs/${id}/detail" | jq '{
    id,
    mode,
    strategy,
    status,
    files_copied,
    bytes_copied,
    error
  }'
}

case_zip_overwrite() {
  header "Lab07 – ZIP_FIRST overwrite (many small files)"

  local SRC="dev_data/src_overwrite_zip_01"
  local DST="dev_data/dst_overwrite_zip_01"

  echo "Resetting test data for ZIP_FIRST..."
  rm -rf "${SRC}" "${DST}"

  python - << 'PYEOF'
from pathlib import Path

src = Path("dev_data/src_overwrite_zip_01")
src.mkdir(parents=True, exist_ok=True)

N = 2000
for i in range(N):
    p = src / f"file_{i:04d}.txt"
    p.write_text(f"overwrite zip test {i}\n" + "x" * 1024)
PYEOF

  echo "Source overview (ZIP_FIRST):"
  find "${SRC}" -type f | wc -l
  du -sh "${SRC}"

  # 1ª execução – deve ser SUCCESS
  header "ZIP_FIRST – first run (should be SUCCESS)"
  local id1
  id1=$(post_job "/data/src_overwrite_zip_01" "/data/dst_overwrite_zip_01" "copy")
  wait_for_job "${id1}"
  print_job_summary "${id1}"

  echo
  echo "Destination after first ZIP_FIRST:"
  find "${DST}" -maxdepth 2 -type f | head
  echo "File count:"
  find "${DST}" -type f | wc -l
  du -sh "${DST}"

  # 2ª execução – deve FALHAR por overwrite (dest já existe)
  header "ZIP_FIRST – second run (should FAIL: Destination already exists)"
  local id2
  id2=$(post_job "/data/src_overwrite_zip_01" "/data/dst_overwrite_zip_01" "copy")
  wait_for_job "${id2}"
  print_job_summary "${id2}"

  echo
  echo "Destination after second ZIP_FIRST (should be unchanged):"
  find "${DST}" -type f | wc -l
  du -sh "${DST}"
}

case_direct_overwrite() {
  header "Lab07 – DIRECT overwrite (single big file)"

  local SRC="dev_data/src_overwrite_direct_01"
  local DST="dev_data/dst_overwrite_direct_01"

  echo "Resetting test data for DIRECT..."
  rm -rf "${SRC}" "${DST}"
  mkdir -p "${SRC}"

  dd if=/dev/zero of="${SRC}/big_01GiB.bin" bs=1m count=1024
  echo "Source overview (DIRECT):"
  du -sh "${SRC}"
  ls "${SRC}"

  # 1ª execução – deve ser SUCCESS
  header "DIRECT – first run (should be SUCCESS)"
  local id1
  id1=$(post_job "/data/src_overwrite_direct_01" "/data/dst_overwrite_direct_01" "copy")
  wait_for_job "${id1}"
  print_job_summary "${id1}"

  echo
  echo "Destination after first DIRECT:"
  find "${DST}" -maxdepth 3 -type f
  du -sh "${SRC}" "${DST}"

  # 2ª execução – deve FALHAR por overwrite (dest/<basename> já existe)
  header "DIRECT – second run (should FAIL: Destination already exists)"
  local id2
  id2=$(post_job "/data/src_overwrite_direct_01" "/data/dst_overwrite_direct_01" "copy")
  wait_for_job "${id2}"
  print_job_summary "${id2}"

  echo
  echo "Destination after second DIRECT (should be unchanged):"
  find "${DST}" -maxdepth 3 -type f
  du -sh "${SRC}" "${DST}"
}

main() {
  cd /Users/pedroc.ampos/Desktop/Kettter3/ketter3

  if [ ! -d "dev_data" ]; then
    echo "ERROR: dev_data folder not found. Run this from the repo root or adjust the path."
    exit 1
  fi

  check_api
  case_zip_overwrite
  case_direct_overwrite

  header "Lab07 – overwrite semantics test finished"
  echo "Review the summaries above (status, error) to confirm:"
  echo "- 1st ZIP_FIRST and DIRECT: success"
  echo "- 2nd ZIP_FIRST and DIRECT: failed with 'Destination already exists: ...'"
}

main "$@"
