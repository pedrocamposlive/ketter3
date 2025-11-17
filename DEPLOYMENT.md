# Ketter 3.0 - Deployment Guide

**Production-Ready Native Deployment**

---

## Overview

Ketter 3.0 runs **natively** on macOS and Windows, providing **direct filesystem access** without Docker limitations. This architecture enables:

 Access to ANY mounted volume (Nexis, EditShare, SANs, network drives)
 Cross-platform support (Mac + Windows)
 Zero volume mapping configuration
 Dynamic detection of mounted volumes
 Better performance (no Docker overhead)

---

## Prerequisites

### macOS Requirements
- macOS 11 (Big Sur) or newer
- Homebrew (will be installed automatically if missing)
- Admin privileges for initial setup

### Windows Requirements
- Windows 10/11 or Windows Server 2019+
- Administrator privileges
- PowerShell 5.1+

---

## Installation

### macOS Installation

**1. Clone or copy Ketter to the server:**
```bash
cd ~/Desktop
git clone <ketter-repo> Ketter3
# OR extract from ZIP
```

**2. Run the installer:**
```bash
cd Ketter3
chmod +x installers/mac/install.sh
./installers/mac/install.sh
```

**3. Wait for installation (5-10 minutes)**

The installer will:
-  Install Homebrew (if needed)
-  Install Python 3.11
-  Install PostgreSQL 15
-  Install Redis
-  Install Node.js 20
-  Install Python dependencies
-  Create database and run migrations
-  Create macOS services (LaunchAgents)
-  Start all services

**4. Access Ketter:**
```
http://localhost:3000
```

**Done!** Ketter is now running as a native macOS application with full filesystem access.

---

### Windows Installation

**1. Copy Ketter to the server:**
```
C:\Ketter3\
```

**2. Run the installer as Administrator:**
```
Right-click installers\windows\install.bat
Select "Run as administrator"
```

**3. Follow installation prompts**

The installer will guide you to install (if not present):
- Python 3.11
- PostgreSQL 15
- Redis
- Node.js 20
- NSSM (service manager)

Then it will:
-  Install Python dependencies
-  Create database and run migrations
-  Create Windows services
-  Start all services

**4. Access Ketter:**
```
http://localhost:3000
```

**Done!** Ketter is now running as Windows services with full filesystem access.

---

## Service Management

### macOS

**View logs:**
```bash
tail -f ~/Library/Logs/ketter-api.log
tail -f ~/Library/Logs/ketter-worker.log
tail -f ~/Library/Logs/ketter-frontend.log
```

**Restart services:**
```bash
cd ~/Desktop/Ketter3
./installers/mac/restart.sh
```

**Stop services:**
```bash
launchctl unload ~/Library/LaunchAgents/com.ketter.*.plist
```

**Start services:**
```bash
launchctl load ~/Library/LaunchAgents/com.ketter.*.plist
```

**Check if services are running:**
```bash
launchctl list | grep ketter
```

---

### Windows

**View logs:**
```
notepad C:\Ketter3\logs\api.log
notepad C:\Ketter3\logs\worker.log
notepad C:\Ketter3\logs\frontend.log
```

**Service management:**
```batch
REM Restart services
nssm restart KetterAPI
nssm restart KetterWorker
nssm restart KetterFrontend

REM Stop services
nssm stop KetterAPI
nssm stop KetterWorker
nssm stop KetterFrontend

REM Start services
nssm start KetterAPI
nssm start KetterWorker
nssm start KetterFrontend

REM Check status
nssm status KetterAPI
```

**Or use Windows Services GUI:**
```
services.msc
Look for: Ketter API, Ketter Worker, Ketter Frontend
```

---

## Configuration

### Server-Specific Configuration

Edit `ketter.config.yml` in the Ketter directory:

```yaml
server:
  name: "Mac-Studio-Finalizacao"  # Change per server
  location: "Sala 2"               # Change per server

# Optional: Path shortcuts (not mandatory)
path_shortcuts:
  # macOS
  nexis: "/Volumes/Nexis"
  shared: "/Users/Shared"

  # Windows
  # nexis: "X:\\"
  # shared: "C:\\Shared"
```

**Important:** Shortcuts are optional helpers. Operators can still type any path directly in the UI.

---

## Filesystem Access

### How It Works

**Native deployment = Direct filesystem access**

```
Operator types in UI: /Volumes/Nexis/Project/Audio
                           ↓
Ketter running natively sees the Mac filesystem
                           ↓
                     Direct access
```

**No Docker mapping needed!**

### macOS Paths

Ketter can access:
-  `/Volumes/VolumeName` - All mounted volumes (Nexis, EditShare, USB, etc.)
-  `/Users/username/...` - User directories
-  `/Users/Shared/...` - Shared folders
-  Any path the Mac user has permissions to read

### Windows Paths

Ketter can access:
-  `C:\`, `D:\`, `E:\` - Local drives
-  `X:\`, `Y:\`, `Z:\` - Mapped network drives
-  `\\ServerName\Share\` - UNC paths (if mapped)
-  Any path the Windows user has permissions to read

---

## Updating Ketter

### macOS Update

```bash
cd ~/Desktop/Ketter3
git pull  # Or extract new version

pip3 install -r requirements.txt
cd frontend && npm install && cd ..

alembic upgrade head  # Database migrations

./installers/mac/restart.sh
```

### Windows Update

```batch
cd C:\Ketter3
git pull

python -m pip install -r requirements.txt
cd frontend
npm install
cd ..

alembic upgrade head

nssm restart KetterAPI
nssm restart KetterWorker
nssm restart KetterFrontend
```

---

## Troubleshooting

### macOS

**Services not starting:**
```bash
# Check logs
tail -50 ~/Library/Logs/ketter-api-error.log

# Check if ports are in use
lsof -i :8000  # API
lsof -i :3000  # Frontend
lsof -i :6379  # Redis
lsof -i :5432  # PostgreSQL

# Restart PostgreSQL/Redis
brew services restart postgresql@15
brew services restart redis
```

**Database connection errors:**
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Test connection
psql -U $(whoami) -d ketter -c "SELECT 1;"
```

### Windows

**Services not starting:**
```batch
REM Check logs
notepad C:\Ketter3\logs\api-error.log

REM Check if ports are in use
netstat -ano | findstr :8000
netstat -ano | findstr :3000

REM Check PostgreSQL service
sc query postgresql-x64-15

REM Check Redis service
sc query Redis
```

**Database connection errors:**
```batch
REM Test PostgreSQL connection
psql -U postgres -d ketter -c "SELECT 1;"
```

---

## Uninstallation

### macOS

```bash
cd ~/Desktop/Ketter3
./installers/mac/uninstall.sh

# Optional: Remove database
dropdb ketter

# Optional: Remove PostgreSQL/Redis
brew uninstall postgresql@15 redis
```

### Windows

```batch
cd C:\Ketter3
installers\windows\uninstall.bat

REM Optional: Remove database
dropdb -U postgres ketter

REM Optional: Uninstall via Control Panel
REM - PostgreSQL
REM - Redis
REM - Python
REM - Node.js
```

---

## Multi-Server Deployment

### Typical Produtora Setup

**Scenario:** 3 Mac Studios + 2 Windows PCs

**Mac Studio 1 (Finalizacao):**
- Acessa: /Volumes/Nexis, /Users/Shared
- Config: `server.name = "Mac-Studio-Finalizacao"`

**Mac Studio 2 (Ingest):**
- Acessa: /Volumes/EditShare, /Users/Shared
- Config: `server.name = "Mac-Studio-Ingest"`

**Windows PC 1 (Backup):**
- Acessa: D:\, Y:\Backup
- Config: `server.name = "Win-Backup-01"`

**Each server:**
1. Run installer
2. Edit `ketter.config.yml` (server name only)
3. Access http://localhost:3000
4. Operators create transfers using paths specific to that server

**No central configuration needed** - each Ketter instance is independent.

---

## Security Considerations

### File Permissions

Ketter runs as:
- **macOS:** Current user (same permissions as logged-in user)
- **Windows:** Service user (configure via NSSM if needed)

**Best practice:** Run Ketter as a user with:
-  Read access to source locations
-  Write access to destination locations
-  Avoid running as root/Administrator (not required)

### Network Access

By default:
- API binds to `0.0.0.0:8000` (accessible from network)
- Frontend binds to `0.0.0.0:3000`

**For production:**
- Consider firewall rules to restrict access
- Use reverse proxy (nginx/Apache) for HTTPS
- Add authentication layer if needed

---

## Performance Tuning

### Large File Transfers (500GB+)

**PostgreSQL:**
```bash
# Increase max_connections if needed
psql -U postgres -c "ALTER SYSTEM SET max_connections = 100;"
```

**Redis:**
```bash
# Increase maxmemory if many concurrent transfers
redis-cli CONFIG SET maxmemory 2gb
```

### Multiple Workers

**macOS:** Edit `~/Library/LaunchAgents/com.ketter.worker.plist`
**Windows:** Create additional worker services with NSSM

```bash
# macOS - copy and modify plist for worker-2, worker-3, etc.
# Windows
nssm install KetterWorker2 python -m rq worker default
```

---

## Docker for Development Only

**Docker is kept ONLY for local development:**

```bash
# Dev environment (Docker)
docker-compose up -d

# Production (Native)
./installers/mac/install.sh
```

**Why?**
- Dev: Isolated environment, fast setup for coding
- Prod: Native access, better performance, zero config

---

## Support

**Logs location:**
- macOS: `~/Library/Logs/ketter-*.log`
- Windows: `C:\Ketter3\logs\*.log`

**Database:**
- Name: `ketter`
- Access: `psql -d ketter`

**Common issues:**
1. Port already in use → Check logs, kill conflicting process
2. Database connection failed → Check PostgreSQL service
3. Redis connection failed → Check Redis service
4. Path not found → Verify volume is mounted on the server

---

**Production-ready deployment. Native filesystem access. Cross-platform support.**
