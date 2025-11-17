"""
Ketter 3.0 - Main FastAPI Application
Minimal Reliable Core (MRC) principles
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from datetime import datetime, timezone
import redis

from app.database import get_db, check_db_connection
from app.routers import transfers, volumes

# Inicializa FastAPI app
app = FastAPI(
    title="Ketter 3.0 API",
    description="File transfer system with triple SHA-256 verification",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - SECURE configuration
# Origins are configured via CORS_ORIGINS environment variable
# Default: allow localhost dev ports for UI (Vite 5173 + fallback ports)
# Production: Must explicitly set allowed origins (comma-separated)
default_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
]
cors_origins_str = os.getenv("CORS_ORIGINS", ",".join(default_cors_origins))
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

# Log CORS configuration on startup (security audit trail)
print(f" CORS: Allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # SECURE: Whitelist only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods
    # Allow UI client identification header + auth/content-type
    allow_headers=["Content-Type", "Authorization", "X-Ketter-Client"],
)

# Include routers
app.include_router(transfers.router)
app.include_router(volumes.router)

# Health check endpoint (requerido pelo Docker healthcheck)
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Verifica se a API está respondendo

    MRC: Simple health check - apenas verifica se API está up
    Para verificações mais detalhadas, use /status
    """
    return {
        "status": "healthy",
        "service": "ketter-api",
        "version": "3.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": os.getenv("APP_ENV", "development")
    }

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint
    Informações básicas da API
    """
    return {
        "name": "Ketter 3.0 API",
        "version": "3.0.0",
        "description": "File transfer system with triple SHA-256 verification",
        "docs": "/docs",
        "health": "/health"
    }

# Status endpoint (mais detalhado que health)
@app.get("/status")
async def status():
    """
    Status endpoint
    Informações detalhadas sobre o sistema

    Verifica:
    - API: Sempre operational se endpoint responde
    - Database: Conexão PostgreSQL
    - Redis: Conexão Redis (para RQ)
    - Worker: Status do RQ worker (via Redis)
    """
    # Check database
    db_status = "connected" if check_db_connection() else "disconnected"

    # Check redis
    redis_status = "disconnected"
    try:
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
        redis_client.ping()
        redis_status = "connected"
    except Exception:
        pass

    # Check worker (via Redis)
    worker_status = "unknown"
    try:
        if redis_status == "connected":
            # Check if there are workers registered in RQ
            from rq import Worker
            workers = Worker.all(connection=redis_client)
            worker_status = f"{len(workers)} worker(s)" if workers else "no workers"
    except Exception:
        pass

    return {
        "api": "operational",
        "database": db_status,
        "redis": redis_status,
        "worker": worker_status,
        "version": "3.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Executado ao iniciar a aplicação
    """
    print(" Ketter 3.0 API iniciando...")
    print(f" Ambiente: {os.getenv('APP_ENV', 'development')}")
    print(f" Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Executado ao desligar a aplicação
    """
    print(" Ketter 3.0 API encerrando...")
