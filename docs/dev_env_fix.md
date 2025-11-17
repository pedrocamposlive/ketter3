# dev_env_fix.md
### Objective
Create a macOS-compatible environment fix script named `dev_env_fix.sh`.

### Codex Must Generate a Script That:
1. Installs Redis (brew)
2. Starts Redis (brew services)
3. Installs redis-cli if missing
4. Installs Python deps:
   - rq
   - uvicorn
5. Ensures correct PATH export
6. Runs a quick validation:
   - `redis-cli ping`
   - python -c "import rq" (OK)
   - python -c "import uvicorn" (OK)

### Deliverable
Codex must output the full script named:

```
dev_env_fix.sh
```

### Final Instruction to Codex
**Execute everything in this file and output ONLY the final script.**
