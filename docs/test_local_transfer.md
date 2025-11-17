# test_local_transfer.md
### Objective
Run a full Desktop→Desktop transfer test in local environment.

---

## Required Steps For Codex

### 1. Validate TransferCreate
Codex must create a payload:
- source_path: ~/Desktop/source_test.mov
- destination_path: ~/Desktop/dest_test.mov
- operation_mode: copy

### 2. Validate HTTP POST
Codex must:
- simulate POST /transfers
- verify HTTP 201
- confirm DB insert

### 3. Validate Redis Queue
Codex must:
- simulate job creation
- validate worker consumption

### 4. Validate copy_engine
Codex must:
- simulate path normalization
- simulate file copy
- simulate SHA-256 verification

### 5. Final Deliverable
Codex must output:

```
local_transfer_test_report.md
```

### Final Instruction to Codex
**Execute everything in this file and output ONLY the report.**
