#!/bin/bash

echo "=== Ketter UI + Backend Smoke Test ==="

echo "[1] Checking backend health..."
curl -s http://localhost:8000/health | jq .

echo "[2] Checking UI delivery..."
curl -I http://localhost:8000

echo "[3] Checking static assets..."
curl -I http://localhost:8000/assets/index.js
curl -I http://localhost:8000/assets/index.css

echo "[4] Checking Transfers API..."
curl -s http://localhost:8000/transfers | jq .

echo "[5] Checking Audit API..."
curl -s http://localhost:8000/audit/logs | jq .

echo "[6] Checking Settings API..."
curl -s http://localhost:8000/settings/volumes | jq .

echo "--- Smoke test complete ---"
echo "Abra http://localhost:8000 no navegador e siga o checklist docs/SMOKE_TEST_UI.md"

