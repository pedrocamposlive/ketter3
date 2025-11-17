#!/bin/bash

echo "Iniciando Ketter 3.0..."
echo ""

# Para tudo
echo "Parando containers antigos..."
docker-compose down -v 2>/dev/null

echo "Aguardando 3 segundos..."
sleep 3

# Inicia tudo
echo "Iniciando Docker Compose..."
docker-compose up -d

# Aguarda services ficarem prontos
echo "Aguardando services ficarem prontos..."
sleep 15

# Verifica se API está saudável
echo "Verificando saúde da API..."
for i in {1..30}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "API está pronta!"
    break
  fi
  echo "Tentativa $i/30 - aguardando API..."
  sleep 2
done

# Executa migrations
echo "Executando migrations do banco de dados..."
docker-compose exec -T api alembic upgrade head

echo ""
echo "========================================================"
echo "KETTER 3.0 PRONTO!"
echo "========================================================"
echo ""
echo "Frontend: http://localhost:3000"
echo "API:      http://localhost:8000"
echo "Database: localhost:5432"
echo "Redis:    localhost:6379"
echo ""
echo "========================================================"
