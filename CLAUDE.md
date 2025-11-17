# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ketter 3.0** is a reliable file transfer system designed for production media workflows. It's a complete rebuild from Ketter 2.0, following a "Minimal Reliable Core (MRC)" philosophy that prioritizes simplicity, reliability, and transparency over features.

**Core Mission:** Transfer large files (500+ GB) with triple SHA-256 checksum verification, zero data loss, and professional audit trails.

## Architecture

The system follows a clean separation of concerns:

```

 Frontend React (single main screen)
  (Web)  

      REST

   API    FastAPI (simple endpoints)

     
     
 
Worker  DB  PostgreSQL
 (RQ)  

```

**Components:**
- **Backend API:** FastAPI for REST endpoints
- **Worker:** RQ (Redis Queue) for async file operations
- **Database:** PostgreSQL for reliability and transaction safety
- **Frontend:** React with single operational view
- **Copy Engine:** Core file transfer with SHA-256 verification

## Technology Stack

- **Python + FastAPI** — Backend (mature for I/O operations)
- **PostgreSQL** — Database (ACID compliance, audit trails)
- **RQ/Redis** — Job queue (simple, traceable)
- **React** — Frontend (single clear operational UI)
- **Docker** — Containerization (robust from Day 1)

## Development Philosophy

**Minimal Reliable Core (MRC) Principles:**

1. **Simplicidade > Funcionalidade** — Simple is better than feature-rich
2. **Confiabilidade > Performance** — Reliability beats speed
3. **Transparência > Automação oculta** — Explicit over implicit
4. **Testes > Intuição** — Test-driven over assumptions
5. **Código limpo > Código esperto** — Clean over clever

## What This System Does (MVP Scope)

**Core Features (6 only):**
1. Manual file/folder selection
2. Triple SHA-256 checksum verification (source, destination, final)
3. Pre-copy disk space validation
4. Professional PDF transfer reports
5. 30-day transfer history
6. Clear operator-friendly UI

**Explicitly NOT in MVP:**
-  Automatic watchfolders
-  Intelligent packaging
-  Schedulers/Cron
-  WebSocket real-time updates
-  Grafana/Prometheus monitoring
-  Multi-user support
-  Configurable policies

## Development Timeline (4 Weeks)

| Week | Deliverable | Technical Goal |
|------|-------------|----------------|
| 1 | Docker + Database + Copy Engine | Copy 1 file with checksum verification |
| 2 | API + Worker | Transfer via API functional |
| 3 | Frontend Web | Operator can complete full workflow |
| 4 | Reports + Tests + Docs | Production-ready system |

## Success Criteria

**Functional:**
- Copy 500 GB without errors
- 100% checksum reliability
- Professional PDF reports
- 30-day history retention

**Operational:**
- Docker works without workarounds
- Zero critical bugs
- Complete documentation
- Operator tested for 1 week

## Key Architectural Decisions

From the planning documents, these technical choices were made:

1. **Python over Node.js** — Better I/O maturity for large file operations
2. **PostgreSQL over MongoDB** — ACID compliance critical for audit trails
3. **RQ over Celery** — Simpler queue management, easier debugging
4. **FastAPI over Flask/Django** — Modern async support, auto-documentation
5. **Docker-first** — Eliminates deployment inconsistencies from 2.0

## Lessons from Ketter 2.0

**Avoid these patterns:**
- Adding features before core is solid
- Fragile Docker configurations
- Complex infrastructure layers
- Hidden automation without transparency

**Follow these patterns:**
- Test from Day 1
- Keep Docker robust and simple
- Explicit is better than implicit
- Delete code rather than add code

## Code Quality Standards

- **Test Coverage:** 100% for core copy engine
- **Code Simplicity:** Target ~2000 LOC total (vs 8000 in 2.0)
- **Documentation:** Every module must have clear purpose
- **Error Handling:** User-friendly messages, no cryptic errors

## When Working on This Codebase

1. **Start with tests** — TDD from the beginning
2. **Keep it simple** — If adding complexity, justify it
3. **Verify checksums** — Every file operation must be verifiable
4. **Think operator-first** — UI/UX for non-technical users
5. **Docker always works** — No workarounds or manual fixes

## Project Status

As of project initialization, this is a **greenfield project**. The comprehensive planning documentation exists in README.md, but implementation has not yet begun. Follow the 4-week timeline and refer to the referenced specification documents when they are created.
