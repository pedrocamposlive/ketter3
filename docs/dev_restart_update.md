# dev_restart_update.md
### Objective
Update the `dev_restart.sh` script to fully support macOS, including:
- sudo-aware port killing  
- detection of uvicorn, rq, redis  
- correct PATH injection  
- Homebrew Redis startup  
- worker auto-spawn  
- API + Redis + Worker validation  
- colored log output  

### Required Changes
Codex must:
1. Load the existing `dev_restart.sh` from the repository.
2. Replace it with a fully updated, macOS-optimized version:
   - Adds automatic PID kill via sudo if necessary.
   - Ensures Redis is installed and running (brew services).
   - Ensures redis-cli is found in PATH.
   - Ensures RQ worker uses the same Python environment.
   - Ensures backend starts cleanly on port 8000.
   - Provides green/red colored messages.
   - Validates environment at the end.

### Deliverable
Codex must output the **full updated script** with all fixes applied, ready to overwrite the current version.

### Final Instruction to Codex
**Execute everything in this file and output ONLY the final updated `dev_restart.sh`.**
