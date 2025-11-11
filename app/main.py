"""
Ketter 3.0 - Main FastAPI Application
Minimal Reliable Core (MRC) principles
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from datetime import datetime
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

# CORS middleware (configurar adequadamente em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restringir em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        "timestamp": datetime.utcnow().isoformat(),
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
        "timestamp": datetime.utcnow().isoformat()
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
