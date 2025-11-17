# Ketter 3.0 - Postgres via Docker (Setup Oficial)

Este documento define o procedimento padrão para rodar o banco de dados Postgres 14 isolado via Docker, evitando conflitos com instalações locais e garantindo consistência de ambiente.

------------------------------------------------------------
1. Pré-requisitos
------------------------------------------------------------

- Docker Desktop instalado no macOS
- Docker Desktop deve estar em estado “Docker is running”
- Porta 5432 livre (qualquer Postgres local deve estar parado)

Verifique:
  docker info
  lsof -i :5432

------------------------------------------------------------
2. Subir Postgres via Docker
------------------------------------------------------------

Execute:

  docker run -d \
    --name ketter-postgres \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=ketter \
    -p 5432:5432 \
    postgres:14

Confirme que está rodando:

  docker ps

Teste a conexão:

  docker exec -it ketter-postgres psql -U postgres -d ketter -c "\dt"

------------------------------------------------------------
3. Remover Postgres local (opcional)
------------------------------------------------------------

Se houver conflito com Postgres nativo ou Homebrew:

  brew services stop postgresql@14
  brew uninstall postgresql@14

------------------------------------------------------------
4. Credenciais dentro do Ketter
------------------------------------------------------------

No arquivo .env:

  POSTGRES_DB=ketter
  POSTGRES_USER=postgres
  POSTGRES_PASSWORD=postgres
  POSTGRES_PORT=5432
  POSTGRES_HOST=localhost

------------------------------------------------------------
5. Reinicializar o ambiente Ketter
------------------------------------------------------------

  ./scripts/dev_restart_docker.sh

------------------------------------------------------------
6. Testes
------------------------------------------------------------

Verificar API:
  curl http://localhost:8000/health

Verificar Redis:
  redis-cli ping

Criar Transfer via UI:
  VITE_API_URL=http://localhost:8000 npm run dev
