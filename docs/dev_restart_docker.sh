#!/bin/bash

set -e

echo "Ketter 3.0 - Docker Restart Script"

echo "Step 1: Garantindo que Postgres local não está ativo..."
if brew services list | grep -q "postgresql"; then
    brew services stop postgresql@14 || true
fi

echo "Step 2: Subindo Postgres via Docker..."
docker rm -f ketter-postgres 2>/dev/null || true

docker run -d \
  --name ketter-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ketter \
  -p 5432:5432 \
  postgres:14

echo "Aguardando Postgres iniciar..."
sleep 5

echo "Testando Postgres..."
docker exec ketter-postgres psql -U postgres -d ketter -c "SELECT 1;" >/dev/null

echo "Postgres OK."

echo "Step 3: Subindo API (uvicorn)..."
pkill -f "uvicorn" || true
sleep 1

nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
  >/tmp/ketter_api.log 2>&1 &

sleep 3

echo "Testando /health..."
curl -s http://localhost:8000/health || {
  echo "API não iniciou."
  exit 1
}

echo "API OK."

echo "Step 4: Subindo RQ Worker..."
pkill -f "rq worker" || true
sleep 1

nohup rq worker default \
  --url redis://localhost:6379 \
  >/tmp/ketter_worker.log 2>&1 &

sleep 2

echo "Ambiente pronto para testes."
