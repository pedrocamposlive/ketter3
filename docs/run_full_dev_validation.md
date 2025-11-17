Ketter V3 — Full Development Environment Validation
Objective

Use the helper script dev_restart.sh to restore the backend, Redis, and worker environments, then execute full transfer tests (Desktop→Desktop), API checks, UI integration checks, and worker execution verification.

1. Load and Validate the Script

Load the script located in the repository:

./dev_restart.sh


Confirm that it performs the following steps:

kills any process on port 8000

starts Redis (docker-compose or brew)

starts the backend via uvicorn

starts the RQ worker

finishes with a ready environment

2. Execute the Script

Simulate executing:

bash ./dev_restart.sh


Track outputs and detect any errors:

permission issues

missing dependencies

uvicorn startup failures

redis connectivity problems

worker failures

3. Validate Backend Availability

After running the script:

confirm port 8000 is now open

confirm the backend responds to:

GET http://localhost:8000/health


or

GET http://localhost:8000/docs


confirm config loads 8 volumes (Desktop/Documents/Downloads included)

4. Validate Redis & Worker

Execute or simulate:

redis-cli ping


Expected:

PONG


Check worker:

It must connect to Redis

It must announce itself as listening on the “default” queue

5. Validate TransferCreate Logic

Perform a simulated Desktop→Desktop validation:

TransferCreate(
  source_path=/Users/<USER>/Desktop/source.mov,
  destination_path=/Users/<USER>/Desktop/dest.mov,
  operation_mode=copy,
  settle_time_seconds=30
)


Expected: validation passes.

6. Validate HTTP /transfers

Simulate:

POST http://localhost:8000/transfers


With the correct JSON payload.

Expected:

HTTP 201

Transfer entry created

DB row committed

job enqueued in Redis

7. Validate Worker Execution

Simulate the worker handling the job:

copy_engine runs

path security passes

file copy occurs

checksum is computed

audit logs are created

transfer status changes accordingly

8. Validate Frontend (Optional Step)

Simulate npm run dev pointing to:

VITE_API_URL=http://localhost:8000


UI must:

send OPTIONS (200)

send POST (201)

display the transfer in TransferProgress

show real-time updates

9. Final Deliverable

Codex must produce a final file:

dev_validation_report.md


Containing:

execution trace of dev_restart.sh

validated steps

failures (if any)

recommended fixes

confirmation that Desktop→Desktop transfers work end-to-end

Final Instruction to Codex

Execute every task in this file and generate the final file dev_validation_report.md.
Your response must contain only the content of this final file.
No extra text, no explanations, no emojis.
