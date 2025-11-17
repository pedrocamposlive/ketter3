# Test Plan

- Activate the new environment: `source .venv/bin/activate`.
- Verify PostgreSQL service: `brew services list | grep postgresql@16` and `pg_isready`.
- Confirm DB setup by connecting as ketter_user: `PGPASSWORD=ketter_user_pass psql -U ketter_user -d ketter -h 127.0.0.1 -c '\dt'`.
- Redis check: `nc -z 127.0.0.1 6379`.
- Run Alembic again if needed: `alembic upgrade head`.
- Launch backend manually: `uvicorn app.main:app --host 0.0.0.0 --port 8000` and hit the health endpoint or main route.

Optional: run project-specific tests (`pytest`, integration scripts) once the services are up.
