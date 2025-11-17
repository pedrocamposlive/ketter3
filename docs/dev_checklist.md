 dev_checklist.md
### Ketter 3.0 — Local Environment Validation Checklist

This checklist ensures a fully working local environment.

---

## 1. Port 8000 Status
- Ensure no process is using port 8000.
- If needed, Codex should instruct how to kill the PID.

---

## 2. Redis Validation
Codex must:
- verify Redis is installed (`brew list redis`)
- validate redis-server is active (`brew services list`)
- verify `redis-cli ping` returns `PONG`
- instruct how to fix Redis if offline

---

## 3. Backend Validation
Codex must:
- verify uvicorn can bind to port 8000
- ensure `app.main:app` loads correctly
- ensure Desktop/Documents/Downloads volumes are attached

---

## 4. Worker Validation
Codex must:
- ensure worker can connect to Redis
- ensure default queue is active
- ensure worker is ready to process transfers

---

## 5. Transfer Create Test
Codex must perform:
- TransferCreate validation
- POST /transfers
- DB entry verification
- Redis queue verification

---

## 6. UI Validation
Codex must simulate:
- OPTIONS /transfers (200)
- POST /transfers (201)
- transfer visible in UI state

---

### Final Deliverable
Codex must produce a markdown file:

```
dev_checklist_report.md
```

containing the results of each step.

### Final Instruction to Codex
**Execute everything in this file and output ONLY the final report.**
