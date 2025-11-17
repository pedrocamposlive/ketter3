# Ketter 3.0 - Installers

Native installers for production deployment on macOS and Windows.

**IMPORTANT:** The macOS installer (`install.sh`) has been refactored for a more robust, "offline-first" installation. Please read the updated notes below.

---

## New Installation Model (macOS v3)

The new installer (`install.sh` v3) expects a distribution package that includes **pre-packaged dependencies**. This makes the client-side installation significantly faster and more reliable, as it minimizes downloads.

- **Pre-packaged Python Dependencies:** The package must include a `.venv` directory at the project root with all Python dependencies pre-installed.
- **Pre-packaged Frontend Dependencies:** The package must include a `node_modules` directory inside `frontend/` with all Node.js dependencies pre-installed.
- **Architecture Specificity:** The pre-packaged dependencies are architecture-specific (Apple Silicon `arm64` vs. Intel `x86_64`). The installer will verify the architecture and abort if there is a mismatch.

**Build/Packaging Requirement:** Before creating the distribution zip, you must run `python3.11 -m venv .venv`, activate it, run `pip install -r requirements.txt`, and run `npm install` inside the `frontend` directory on a machine with the target architecture.

---

## Quick Start

### macOS

```bash
# Navigate to the extracted Ketter_Repo directory
cd Ketter_Repo
chmod +x installers/mac/install.sh
./installers/mac/install.sh
```

**Access:** http://localhost:3000

### Windows

```batch
Right-click installers\windows\install.bat
Select "Run as administrator"
```

**Access:** http://localhost:3000

---

## What Gets Installed

### macOS
- **System Dependencies (via Homebrew):**
  - Python 3.11
  - PostgreSQL 15
  - Redis
  - Node.js 20
- **Application Dependencies (Pre-packaged):**
  - Ketter Python dependencies (in `.venv`)
  - Ketter frontend dependencies (in `frontend/node_modules`)
- **Services:**
  - macOS LaunchAgents for API, Worker, and Frontend

### Windows
- Python 3.11 (manual download)
- PostgreSQL 15 (manual download)
- Redis (manual download)
- Node.js 20 (manual download)
- NSSM (service manager)
- Ketter Python dependencies
- Ketter frontend dependencies
- Windows Services

---

## Files

### macOS (`installers/mac/`)
- `install.sh` - Main installer (v3, refactored)
- `restart.sh` - Restart all services
- `uninstall.sh` - Remove services

### Windows (`installers/windows/`)
- `install.bat` - Main installer
- `uninstall.bat` - Remove services

---

## Post-Installation

**1. Verify services are running:**

macOS:
```bash
curl http://localhost:8000/health
curl http://localhost:3000
```

Windows:
```batch
curl http://localhost:8000/health
curl http://localhost:3000
```

**2. Check logs if issues:**

macOS:
- Application Logs: `~/Library/Logs/ketter-*.log`
- Homebrew Logs: `~/Library/Logs/Homebrew/`

Windows: `C:\Ketter3\logs\*.log`

**3. Configure server (optional):**

Edit `ketter.config.yml` to set server name and location.

---

## Troubleshooting

**Services not starting?**
- Check application logs (see paths above).
- Check Homebrew logs if a dependency failed to install.
- Verify PostgreSQL and Redis are running (`brew services list`).
- Check if ports 3000/8000/5432/6379 are available.

**Architecture Mismatch Error?**
- The `install.sh` script detected that the pre-packaged dependencies were built for a different CPU architecture (e.g., Intel vs. Apple Silicon).
- **Solution:** You must rebuild the distribution package on a machine that matches the client's architecture.

**Database errors?**
- Verify PostgreSQL is running (`brew services list | grep postgresql`).
- Test connection: `psql -d ketter`

---

For complete documentation, see: [DEPLOYMENT.md](../DEPLOYMENT.md)