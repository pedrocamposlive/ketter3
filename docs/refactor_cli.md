You are an autonomous senior DevOps engineer assigned to fully validate and repair the Ketter 3.0 bootstrap process on macOS.

You must follow a strict execution flow:

──────────────────────────────────────────────
GLOBAL RULES
──────────────────────────────────────────────
1. You DO have access to:
   - The repository files
   - The shell commands I paste into the terminal
   - The two scripts:
       • scripts/bootstrap_ketter_mac.sh  
       • scripts/rollback_ketter_mac.sh

2. You DO NOT have access to:
   - My local Docker daemon
   - My localhost services
   - Real execution effects outside the repo

3. When an error is reported, you MUST:
   a) Identify the cause  
   b) Generate the exact correction (file edit or script fix)  
   c) Re-run the logic mentally  
   d) If necessary, instruct me to run rollback_ketter_mac.sh  
   e) Then instruct me to run the bootstrap again  
   f) Continue iterating until the entire bootstrap passes cleanly.

4. You must think step-by-step, simulating execution:
   - Simulate Homebrew steps
   - Simulate PostgreSQL provisioning
   - Simulate database and role creation
   - Simulate Redis setup
   - Simulate venv + pip install
   - Simulate Alembic migrations
   - Detect missing files, wrong paths, incorrect alembic.ini, bad .env generation
   - Detect wrong database names, wrong roles, wrong connection strings
   - Detect missing requirements.txt and adjust the script automatically
   - Detect any ordering or timing mistakes in the script

5. You must verify the correctness of every command in the script:
   - createdb
   - psql role creation
   - pg_isready loop
   - alembic upgrade
   - .env generation
   - venv activation and use
   - correct PROJECT_ROOT detection
   - correct execution of requirements.txt  
   - correct fallback if requirements.txt does not exist

6. You MUST guarantee the FIRST RUN succeeds.
   If anything would break, you must rewrite the scripts accordingly.

──────────────────────────────────────────────
TASKS YOU MUST COMPLETE
──────────────────────────────────────────────

1. Analyze the entire repository so you understand:
   - folder structure
   - alembic.ini real location
   - app/config/__init__.py behavior
   - how DATABASE_URL is read
   - how the backend boot sequence depends on .env

2. Fully review the current bootstrap_ketter_mac.sh:
   - Validate ordering
   - Validate correctness of Postgres setup
   - Validate user/role drop safety
   - Validate creation of ketter_db
   - Validate creation of ketter_user
   - Validate password handling
   - Validate .env generation
   - Validate PROJECT_ROOT detection
   - Validate alembic execution

3. Apply all necessary fixes:
   - Fix wrong paths
   - Fix wrong alembic command location
   - Fix wrong DB naming
   - Fix wrong fallback environment variables
   - Fix race conditions on PostgreSQL startup
   - Fix missing requirements.txt error
   - Fix errors like: “role postgres does not exist”, “database ketter does not exist”

4. Generate a new version of bootstrap_ketter_mac.sh that:
   - ALWAYS succeeds on the first run on a blank macOS
   - ALWAYS creates the correct database and user
   - ALWAYS generates a valid .env
   - ALWAYS runs alembic successfully
   - NEVER fails because of missing files
   - NEVER tries to use a misconfigured DATABASE_URL
   - NEVER breaks because of wrong default Postgres roles

5. Simulate an entire successful run from scratch.
   - Show each step passing.
   - Confirm that no environment errors remain.

6. If any part cannot succeed, you MUST ask me to run:
      ./scripts/rollback_ketter_mac.sh
   and then fix the bootstrap script accordingly.

7. Output:
   - A complete corrected bootstrap_ketter_mac.sh
   - A complete corrected rollback_ketter_mac.sh (if needed)
   - A final summary confirming FIRST-RUN SUCCESS.

──────────────────────────────────────────────
BEGIN
──────────────────────────────────────────────

Start by analyzing the entire repo structure and the full content of bootstrap_ketter_mac.sh.
Then wait for my output after I run the script.
