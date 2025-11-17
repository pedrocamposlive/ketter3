Ketter V3 — Local Transfer Validation Plan
Objective

Validate and ensure that the Ketter transfer engine functions correctly for Desktop → Desktop transfers in development mode on macOS.

This test suite verifies the full flow:
UI → API → validation → DB insert → enqueue → worker → copy_engine → audit → UI polling.

1. Required Configuration Updates
1.1 Apply the Codex patch

Ensure the repository contains the updated:

app/config/init.py (with the auto-attach of Desktop/Documents/Downloads)

.env.example

.env with:

ALLOW_USER_DESKTOP=1
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8000

1.2 Restart backend

If running uvicorn:

Ctrl + C
uvicorn app.main:app --reload


If running docker-compose:

docker compose up -d --build api


Backend must load with:

Loaded config: <name> (8 volumes)

2. Manual Validation (Python)

Run:

python - <<'PY'
from app.schemas import TransferCreate

payload = {
    'source_path': '/Users/<USER>/Desktop/test_source.mov',
    'destination_path': '/Users/<USER>/Desktop/test_dest.mov',
    'watch_mode_enabled': False,
    'settle_time_seconds': 30,
    'watch_continuous': False,
    'operation_mode': 'copy'
}

result = TransferCreate(**payload)
print("Validated OK:", result)
PY


Expected:
Path passes validation with no 422 errors.

3. Full Backend Validation
3.1 Create a transfer directly (HTTP)

POST request:

curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -H "X-Ketter-Client: UI" \
  -d '{
    "source_path": "/Users/<USER>/Desktop/test_source.mov",
    "destination_path": "/Users/<USER>/Desktop/test_dest.mov",
    "watch_mode_enabled": false,
    "settle_time_seconds": 30,
    "watch_continuous": false,
    "operation_mode": "copy"
  }'


Expected:

HTTP 201

Transfer object returned (id, timestamps, operation=batch)

3.2 Check DB entry

Verify row exists in transfers table.

3.3 Check Redis queue

Run:

rq info


Expected:
Job enqueued and processed.

4. Frontend Validation
4.1 Start frontend with correct API URL
cd frontend
VITE_API_URL=http://localhost:8000 npm run dev

4.2 Browser test

Open UI at http://localhost:5173

Create a transfer using:

Source: Desktop file

Dest: Desktop file

Observe:

OPTIONS /transfers → 200

POST /transfers → 201

Transfer appears in TransferProgress

Status updates from: pending → copying → verifying → completed

5. Worker + Engine Validation

Verify the worker performs:

Path normalization

File copy/move

Triple SHA-256

AuditLog entries

Status transitions

Confirm the destination file is created on Desktop.

6. Regression Tests

If project contains tests:

pytest tests/test_path_security.py
pytest tests/test_comprehensive_move_copy.py


Confirm unauthorized paths are still blocked while Desktop paths pass.

7. Final Deliverable

Codex must produce a new file named:
local_transfer_validation_report.md
containing:

Root-cause analysis

Execution results

Fix validation

Confirmed pass/fail for all tests above

8. Final Instruction to Codex

Execute every task in this file and generate the final file local_transfer_validation_report.md as your output.
Response must contain only the content of the generated report.
No chatter.
No meta comments.
No emojis.
