# Ketter 3.0

**Production-Grade File Transfer System with Triple SHA-256 Verification**

Reliable file transfer system designed for media production workflows. Handles large files (500+ GB) with zero data loss guarantee through triple checksum verification and complete audit trails.

---

## Features

### Core Features (MVP)
-  **Triple SHA-256 Verification** - Source, Destination, Final verification
-  **Smart Folder Handling** - Auto-ZIP folders (STORE mode, no compression)
-  **Watch Mode** - Wait for folder to stabilize before transfer
-  **Professional PDF Reports** - Complete audit trail and checksums
-  **30-Day Transfer History** - Full audit logs and metrics
-  **Modern Dark UI** - Monochromatic professional interface

### Technical Features
-  **Direct Filesystem Access** - No Docker volume mapping needed
-  **Cross-Platform** - Native support for macOS and Windows
-  **Any Volume Support** - Nexis, EditShare, SANs, network drives, local storage
-  **Async Processing** - RQ worker for background transfers
-  **PostgreSQL Database** - ACID compliance for reliability
-  **RESTful API** - FastAPI with auto-documentation

---

## Quick Start

### macOS

```bash
cd Ketter3
chmod +x installers/mac/install.sh
./installers/mac/install.sh
```

Access: **http://localhost:3000**

### Windows

```batch
Right-click installers\windows\install.bat
Select "Run as administrator"
```

Access: **http://localhost:3000**

---

## Architecture

```

   React UI   http://localhost:3000
  (Frontend) 

        REST API

  FastAPI     http://localhost:8000
   (API)     

       
  
                     
  
 RQ   Redis PostgreSQL
Worker  

```

**Native Deployment:**
- No Docker in production
- Direct filesystem access
- Runs as system services (LaunchAgents on Mac, Windows Services)

---

## System Requirements

### macOS
- macOS 11 (Big Sur) or newer
- Python 3.11+
- PostgreSQL 15
- Redis 7
- Node.js 20

### Windows
- Windows 10/11 or Server 2019+
- Python 3.11+
- PostgreSQL 15
- Redis 3.0+
- Node.js 20

**All dependencies are installed automatically by the installer.**

---

## Usage

### Creating a Transfer

1. **Access UI:** http://localhost:3000
2. **Click "New Transfer"**
3. **Enter paths:**
   - **macOS:** `/Volumes/Nexis/Project/Audio` or `/Users/Shared/Files`
   - **Windows:** `D:\Projects\Audio` or `Y:\NetworkDrive\Files`
4. **Options:**
   - Enable Watch Mode if folder is still receiving files
   - Set Settle Time (default: 30 seconds)
5. **Click "Create Transfer"**

### Monitoring Transfers

- **Active Transfers:** Real-time progress with status badges
- **History:** 30-day retention with filters
- **PDF Reports:** Download complete audit trail per transfer

### Filesystem Access

**Ketter has direct access to:**
-  All mounted volumes (Mac: `/Volumes/*`, Windows: `D:\`, `Y:\`, etc.)
-  Network drives (automatically detected when mounted)
-  User directories
-  Any path the user has read/write permissions to

**No configuration needed** - if you can see it in Finder/Explorer, Ketter can access it.

---

## Deployment

### Single Server

Install on one Mac or Windows server:
```bash
# Mac
./installers/mac/install.sh

# Windows
installers\windows\install.bat
```

Operators access via browser on the same machine: `http://localhost:3000`

### Multiple Servers

Install Ketter on each server independently:

**Example produtora setup:**
- Mac Studio 1 (Finalizacao) - Accesses `/Volumes/Nexis`
- Mac Studio 2 (Ingest) - Accesses `/Volumes/EditShare`
- Windows PC (Backup) - Accesses `Y:\Backup`

Each server runs its own Ketter instance. No central configuration needed.

**Configuration per server:**
Edit `ketter.config.yml`:
```yaml
server:
  name: "Mac-Studio-Finalizacao"  # Change this
  location: "Sala 2"               # Change this
```

---

## Service Management

### macOS

**Logs:**
```bash
tail -f ~/Library/Logs/ketter-api.log
tail -f ~/Library/Logs/ketter-worker.log
```

**Restart:**
```bash
./installers/mac/restart.sh
```

**Stop/Start:**
```bash
launchctl unload ~/Library/LaunchAgents/com.ketter.*.plist
launchctl load ~/Library/LaunchAgents/com.ketter.*.plist
```

### Windows

**Logs:**
```
C:\Ketter3\logs\api.log
C:\Ketter3\logs\worker.log
```

**Restart:**
```batch
nssm restart KetterAPI
nssm restart KetterWorker
nssm restart KetterFrontend
```

**Or use Services GUI:** `services.msc` → Find "Ketter" services

---

## Development

**For development, Docker is still available:**

```bash
# Development environment (Docker)
docker-compose up -d

# Run tests
docker-compose exec api pytest

# Access
http://localhost:3000  # Frontend
http://localhost:8000  # API
```

**Production uses native deployment (see DEPLOYMENT.md)**

---

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[TESTING.md](TESTING.md)** - Test suite documentation
- **[UPDATES_2025-11-05.md](UPDATES_2025-11-05.md)** - Latest changes
- **[installers/README.md](installers/README.md)** - Installer documentation
- **Core project strategy and blueprints** now live under `docs/`. Consult:
  - `docs/strategy.md`
  - `docs/blueprint.md`
  - `docs/blueprint-organization.md`
  - `docs/blueprint-hardening.md`
  - `docs/state.md`, `docs/state-organization.md`, `docs/state-hardening.md`

---

## Ketter 3.0 — UI Manus Release

Official Manus release artifacts live in `public/assets/release/ui`. This bundle contains the verified dashboard, transfers, audit, system health, and settings exposures the release team uses for automation, documentation, and QA (see `docs/UI_RELEASE_STRATEGY.md` for process, gating, and manifest requirements).

### Screenshots

Place the finalized artwork into:

- `public/assets/release/ui/dashboard.png`
- `public/assets/release/ui/transfers.png`
- `public/assets/release/ui/audit.png`
- `public/assets/release/ui/system-health.png`
- `public/assets/release/ui/settings.png`

The companion manifest (`public/assets/release/ui/manifest.json`) declares the approved filenames, captions, and review context. The placeholders shipped here ensure the folder structure is validated even when the designer delivers assets later.

### Build instructions

```bash
cd frontend
npm install
npm run build
```

The build generates `dist/`; include the generated bundle in the release package and verify that smoke tests from `docs/SMOKE_TEST_UI.md` pass locally before signing off.

### Backend integration

The frontend communicates with FastAPI via `VITE_API_URL` (defaults to `http://localhost:8000`). Launch the backend before opening the UI:

```bash
uvicorn app.main:app --reload
VITE_API_URL=http://localhost:8000 npm run dev
```

All UI fetches include the `X-Ketter-Client: UI` header. The backend allows only whitelisted origins in `app.main` (CORS middleware) so the dev server must run on `localhost` (port 5173 or a configured host) and the production build must host assets served by FastAPI or a trusted CDN.

### Security highlights

- Keep `X-Ketter-Client` present on every request so FastAPI can distinguish UI traffic.
- Only allow the documented local hosts via the `CORS_ORIGINS` environment variable (`http://localhost:5173`, `http://localhost:3000`, or the final UI domain) to prevent cross-site misuse.
- Point the UI at the signed API base (`VITE_API_URL`) and never proxy the FastAPI backend through the dev server for production releases; the `public/assets/release/ui` bundle is the single source of sanctioned UI assets.

---

## Project Status

** Production Ready**

- **Core System:** 100% complete (SHA-256, copy engine, PDF reports)
- **Week 5 Features:** ZIP Smart + Watch Mode implemented
- **Tests:** 100/100 passing
- **Native Deployment:** macOS and Windows installers
- **Documentation:** Complete

**Recent Updates (2025-11-05):**
-  Monochromatic dark theme
-  Free path input (any volume)
-  Volume validation removed
-  Native installers (Mac + Windows)
-  Direct filesystem access

---

## MRC Principles

Ketter 3.0 follows **Minimal Reliable Core** principles:

1. **Simplicidade > Funcionalidade** - Simple, focused features
2. **Confiabilidade > Performance** - Zero data loss guarantee
3. **Transparência > Automação oculta** - Complete audit trails
4. **Testes > Intuição** - 100% test coverage on core
5. **Código limpo > Código esperto** - Maintainable codebase

---

## Support

**Logs:**
- macOS: `~/Library/Logs/ketter-*.log`
- Windows: `C:\Ketter3\logs\*.log`

**Database:**
```bash
# Connect to database
psql -d ketter  # Mac
psql -U postgres -d ketter  # Windows
```

**Health Check:**
```bash
curl http://localhost:8000/health
curl http://localhost:3000
```

---

## License

Proprietary - Internal use only

---

**Built for production media workflows. Reliable. Simple. Transparent.**
