# Ketter 3.0 - Dockerfile
# Multi-stage build para imagem otimizada

# Stage 1: Builder - Compila dependências
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Instala dependências de build
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - Imagem final limpa
FROM python:3.11-slim-bookworm

# Metadata
LABEL maintainer="Ketter 3.0 Team"
LABEL description="File transfer system with triple SHA-256 verification"
LABEL version="3.0.0"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    USER=ketter \
    UID=1000 \
    GID=1000

# Instala apenas runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root
RUN groupadd -g ${GID} ${USER} && \
    useradd -u ${UID} -g ${GID} -s /bin/bash -m ${USER}

# Cria diretórios de trabalho
WORKDIR ${APP_HOME}

# Copia dependências do builder
COPY --from=builder --chown=${USER}:${USER} /root/.local /home/${USER}/.local

# Adiciona binários Python ao PATH
ENV PATH=/home/${USER}/.local/bin:$PATH

# Cria diretórios necessários
RUN mkdir -p /data/transfers && \
    chown -R ${USER}:${USER} /data

# Copia código da aplicação
COPY --chown=${USER}:${USER} . .

# Muda para usuário não-root
USER ${USER}

# Expõe porta da API (FastAPI)
EXPOSE 8000

# Health check (será sobrescrito no docker-compose para endpoints específicos)
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão (será sobrescrito no docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
