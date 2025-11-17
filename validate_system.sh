#!/bin/bash

###############################################################################
# Ketter 3.0 - Complete System Validation (v2.0 - Robust)
#
# Este script valida TODOS os componentes do sistema de forma robusta.
# Cada comando foi testado individualmente antes de ser incluído.
#
# Uso: ./validate_system_v2.sh
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
TOTAL=0

# Failed tests tracking
FAILED_TESTS=()

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_test() {
    TOTAL=$((TOTAL + 1))
    echo -e "\n${YELLOW}[TEST $TOTAL]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}${NC} $1"
    PASSED=$((PASSED + 1))
}

print_fail() {
    echo -e "${RED}${NC} $1"
    FAILED=$((FAILED + 1))
    FAILED_TESTS+=("TEST $TOTAL: $2")
}

print_info() {
    echo -e "  ${CYAN}→${NC} $1"
}

###############################################################################
# PHASE 1: Docker Infrastructure
###############################################################################

print_header "PHASE 1: Docker Infrastructure (6 tests)"

# Test 1
print_test "Docker Compose services running"
if docker-compose ps 2>/dev/null | grep -q "Up"; then
    SERVICE_COUNT=$(docker-compose ps | grep "Up" | wc -l | tr -d ' ')
    print_pass "Docker services are running ($SERVICE_COUNT containers)"
else
    print_fail "Docker services not running" "Docker not running"
    exit 1
fi

# Test 2
print_test "PostgreSQL health"
if docker-compose ps postgres | grep -q "healthy"; then
    POSTGRES_VERSION=$(docker-compose exec -T postgres psql --version 2>/dev/null | grep -o "PostgreSQL [0-9.]*" || echo "PostgreSQL")
    print_pass "PostgreSQL is healthy"
    print_info "$POSTGRES_VERSION on port 5432"
else
    print_fail "PostgreSQL not healthy" "PostgreSQL unhealthy"
fi

# Test 3
print_test "Redis health"
if docker-compose ps redis | grep -q "healthy"; then
    print_pass "Redis is healthy"
    print_info "Redis 7 on port 6379"
else
    print_fail "Redis not healthy" "Redis unhealthy"
fi

# Test 4
print_test "API container health"
if docker-compose ps api | grep -q "healthy"; then
    print_pass "API container is healthy"
    print_info "FastAPI on port 8000"
else
    print_fail "API not healthy" "API unhealthy"
fi

# Test 5
print_test "Worker container status"
if docker-compose ps worker | grep -q "Up"; then
    print_pass "Worker is running"
    print_info "RQ Worker processing queue 'default'"
else
    print_fail "Worker not running" "Worker down"
fi

# Test 6
print_test "Frontend container status"
if docker-compose ps frontend | grep -q "Up"; then
    print_pass "Frontend is running"
    print_info "React + Vite on port 3000"
else
    print_fail "Frontend not running" "Frontend down"
fi

###############################################################################
# PHASE 2: API Endpoints
###############################################################################

print_header "PHASE 2: API Endpoints (5 tests)"

# Test 7
print_test "API health endpoint"
HEALTH_CHECK=$(curl -s http://localhost:8000/health 2>/dev/null)
if echo "$HEALTH_CHECK" | grep -q '"status":"healthy"'; then
    SERVICE_NAME=$(echo "$HEALTH_CHECK" | grep -o '"service":"[^"]*"' | cut -d'"' -f4)
    VERSION=$(echo "$HEALTH_CHECK" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    print_pass "API health endpoint responding"
    print_info "Service: $SERVICE_NAME, Version: $VERSION"
else
    print_fail "API health check failed" "API health endpoint error"
fi

# Test 8
print_test "API status endpoint"
STATUS_CHECK=$(curl -s http://localhost:8000/status 2>/dev/null)
if echo "$STATUS_CHECK" | grep -q '"database"' && echo "$STATUS_CHECK" | grep -q '"redis"'; then
    print_pass "API status endpoint responding"
    print_info "Database and Redis status available"
else
    print_fail "API status check failed" "API status endpoint error"
fi

# Test 9
print_test "API documentation"
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null)
if [ "$DOCS_CODE" = "200" ]; then
    print_pass "API documentation accessible"
    print_info "http://localhost:8000/docs"
else
    print_fail "API docs not accessible (HTTP $DOCS_CODE)" "API docs error"
fi

# Test 10
print_test "API OpenAPI spec"
OPENAPI_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/openapi.json 2>/dev/null)
if [ "$OPENAPI_CODE" = "200" ]; then
    print_pass "OpenAPI spec available"
else
    print_fail "OpenAPI spec not available (HTTP $OPENAPI_CODE)" "OpenAPI error"
fi

# Test 11
print_test "Frontend accessibility"
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
if [ "$FRONTEND_CODE" = "200" ]; then
    print_pass "Frontend is accessible"
    print_info "http://localhost:3000"
else
    print_fail "Frontend not accessible (HTTP $FRONTEND_CODE)" "Frontend error"
fi

###############################################################################
# PHASE 3: Database
###############################################################################

print_header "PHASE 3: Database Operations (3 tests)"

# Test 12
print_test "Database connectivity"
if docker-compose exec -T postgres psql -U ketter -d ketter -c "SELECT 1" >/dev/null 2>&1; then
    print_pass "Database connection successful"
else
    print_fail "Database connection failed" "DB connection error"
fi

# Test 13
print_test "Database schema"
TABLE_COUNT=$(docker-compose exec -T postgres psql -U ketter -d ketter -t -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public';" 2>/dev/null | tr -d ' \n')
if [ "$TABLE_COUNT" -ge "4" ]; then
    print_pass "Database schema complete ($TABLE_COUNT tables)"
    print_info "Tables: transfers, checksums, audit_logs, alembic_version"
else
    print_fail "Database schema incomplete ($TABLE_COUNT tables)" "Schema error"
fi

# Test 14
print_test "Transfers table access"
TRANSFER_COUNT=$(docker-compose exec -T postgres psql -U ketter -d ketter -t -c "SELECT COUNT(*) FROM transfers;" 2>/dev/null | tr -d ' \n')
if [ -n "$TRANSFER_COUNT" ]; then
    print_pass "Transfers table accessible"
    print_info "$TRANSFER_COUNT transfers in database"
else
    print_fail "Cannot access transfers table" "Transfers table error"
fi

###############################################################################
# PHASE 4: Complete Transfer Workflow
###############################################################################

print_header "PHASE 4: Transfer Workflow (8 tests)"

# Test 15
print_test "Creating test file"
TEST_DATA="Ketter 3.0 Validation - $(date '+%Y-%m-%d %H:%M:%S')"
docker-compose exec -T api sh -c "echo '$TEST_DATA' > /data/transfers/validation_test.txt" 2>/dev/null

if docker-compose exec -T api test -f /data/transfers/validation_test.txt 2>/dev/null; then
    FILE_SIZE=$(docker-compose exec -T api stat -c%s /data/transfers/validation_test.txt 2>/dev/null)
    print_pass "Test file created"
    print_info "Size: $FILE_SIZE bytes"
else
    print_fail "Failed to create test file" "File creation error"
    exit 1
fi

# Test 16
print_test "Creating transfer via API"
CREATE_RESPONSE=$(curl -s -X POST http://localhost:8000/transfers \
    -H "Content-Type: application/json" \
    -d '{"source_path":"/data/transfers/validation_test.txt","destination_path":"/data/transfers/validation_test_dest.txt"}' 2>/dev/null)

TRANSFER_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":[0-9]*' | grep -o '[0-9]*')

if [ -n "$TRANSFER_ID" ] && [ "$TRANSFER_ID" -gt 0 ]; then
    print_pass "Transfer created"
    print_info "Transfer ID: $TRANSFER_ID"
else
    print_fail "Failed to create transfer" "Transfer creation error"
    echo "Response: $CREATE_RESPONSE"
    exit 1
fi

# Test 17
print_test "Monitoring transfer completion"
MAX_WAIT=30
ELAPSED=0
FINAL_STATUS="unknown"

while [ $ELAPSED -lt $MAX_WAIT ]; do
    TRANSFER_DATA=$(curl -s http://localhost:8000/transfers/$TRANSFER_ID 2>/dev/null)
    STATUS=$(echo "$TRANSFER_DATA" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

    if [ "$STATUS" = "completed" ]; then
        FINAL_STATUS="completed"
        break
    elif [ "$STATUS" = "failed" ]; then
        FINAL_STATUS="failed"
        ERROR=$(echo "$TRANSFER_DATA" | grep -o '"error_message":"[^"]*"' | cut -d'"' -f4)
        print_fail "Transfer failed: $ERROR" "Transfer failed"
        break
    fi

    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ "$FINAL_STATUS" = "completed" ]; then
    print_pass "Transfer completed"
    print_info "Completed in ${ELAPSED}s"
else
    print_fail "Transfer did not complete (status: $FINAL_STATUS)" "Transfer incomplete"
fi

# Test 18
print_test "Verifying checksums"
CHECKSUMS=$(curl -s http://localhost:8000/transfers/$TRANSFER_ID/checksums 2>/dev/null)
CHECKSUM_COUNT=$(echo "$CHECKSUMS" | grep -o '"checksum_type"' | wc -l | tr -d ' ')

if [ "$CHECKSUM_COUNT" = "3" ]; then
    print_pass "Triple SHA-256 checksums present"

    # Extract checksums
    SOURCE=$(echo "$CHECKSUMS" | grep -A1 '"checksum_type":"source"' | grep '"checksum_value"' | cut -d'"' -f4)
    DEST=$(echo "$CHECKSUMS" | grep -A1 '"checksum_type":"destination"' | grep '"checksum_value"' | cut -d'"' -f4)
    FINAL=$(echo "$CHECKSUMS" | grep -A1 '"checksum_type":"final"' | grep '"checksum_value"' | cut -d'"' -f4)

    print_info "SOURCE:      ${SOURCE:0:16}...${SOURCE: -16}"
    print_info "DESTINATION: ${DEST:0:16}...${DEST: -16}"
    print_info "FINAL:       ${FINAL:0:16}...${FINAL: -16}"

    if [ "$SOURCE" = "$DEST" ] && [ "$SOURCE" = "$FINAL" ]; then
        print_pass "Checksums match perfectly"
    else
        print_fail "Checksums do not match" "Checksum mismatch"
    fi
else
    print_fail "Expected 3 checksums, got $CHECKSUM_COUNT" "Checksum count error"
fi

# Test 19
print_test "Verifying audit trail"
LOGS=$(curl -s http://localhost:8000/transfers/$TRANSFER_ID/logs 2>/dev/null)
LOG_COUNT=$(echo "$LOGS" | grep -o '"total":[0-9]*' | grep -o '[0-9]*')

if [ "$LOG_COUNT" -ge "10" ]; then
    print_pass "Audit trail complete"
    print_info "$LOG_COUNT events logged"

    # Check key events
    if echo "$LOGS" | grep -q '"event_type":"transfer_created"'; then
        print_info " transfer_created event"
    fi
    if echo "$LOGS" | grep -q '"event_type":"transfer_completed"'; then
        print_info " transfer_completed event"
    fi
else
    print_fail "Audit trail incomplete ($LOG_COUNT events)" "Audit trail error"
fi

# Test 20
print_test "Verifying destination file"
if docker-compose exec -T api test -f /data/transfers/validation_test_dest.txt 2>/dev/null; then
    DEST_SIZE=$(docker-compose exec -T api stat -c%s /data/transfers/validation_test_dest.txt 2>/dev/null)
    print_pass "Destination file exists"
    print_info "Size: $DEST_SIZE bytes"

    # Verify file contents match
    SOURCE_HASH=$(docker-compose exec -T api sha256sum /data/transfers/validation_test.txt 2>/dev/null | awk '{print $1}')
    DEST_HASH=$(docker-compose exec -T api sha256sum /data/transfers/validation_test_dest.txt 2>/dev/null | awk '{print $1}')

    if [ "$SOURCE_HASH" = "$DEST_HASH" ]; then
        print_pass "File contents match"
        print_info "SHA-256: ${SOURCE_HASH:0:16}...${SOURCE_HASH: -16}"
    else
        print_fail "File contents do not match" "File content mismatch"
    fi
else
    print_fail "Destination file not found" "Destination file missing"
fi

# Test 21
print_test "PDF report generation"
PDF_CODE=$(curl -s -o /tmp/ketter_validation_report.pdf -w "%{http_code}" http://localhost:8000/transfers/$TRANSFER_ID/report 2>/dev/null)

if [ "$PDF_CODE" = "200" ]; then
    if file /tmp/ketter_validation_report.pdf | grep -q "PDF document"; then
        PDF_SIZE=$(ls -lh /tmp/ketter_validation_report.pdf | awk '{print $5}')
        print_pass "PDF report generated"
        print_info "Size: $PDF_SIZE, saved to /tmp/ketter_validation_report.pdf"
    else
        print_fail "Generated file is not a valid PDF" "PDF validation error"
    fi
else
    print_fail "PDF generation failed (HTTP $PDF_CODE)" "PDF generation error"
fi

# Test 22
print_test "Deleting test transfer"
DELETE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE http://localhost:8000/transfers/$TRANSFER_ID 2>/dev/null)

if [ "$DELETE_CODE" = "204" ]; then
    print_pass "Transfer deleted"
else
    print_fail "Failed to delete transfer (HTTP $DELETE_CODE)" "Delete error"
fi

# Cleanup
docker-compose exec -T api rm -f /data/transfers/validation_test.txt /data/transfers/validation_test_dest.txt 2>/dev/null

###############################################################################
# PHASE 5: Automated Test Suite
###############################################################################

print_header "PHASE 5: Automated Tests (1 test)"

# Test 23
print_test "Running pytest suite (43 tests)"
if docker-compose exec -T api pytest tests/test_models.py tests/test_api.py tests/test_integration.py -q 2>&1 | grep -q "43 passed"; then
    print_pass "All automated tests passed"
    print_info "43/43 tests passed"
else
    print_fail "Some automated tests failed" "Pytest failures"
fi

###############################################################################
# FINAL REPORT
###############################################################################

print_header "VALIDATION REPORT"

echo -e "\n${CYAN}Summary:${NC}"
echo -e "  Total Tests:  ${YELLOW}$TOTAL${NC}"
echo -e "  Passed:       ${GREEN}$PASSED${NC}"
echo -e "  Failed:       ${RED}$FAILED${NC}"
echo -e "  Success Rate: ${CYAN}$(( PASSED * 100 / TOTAL ))%${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN} ALL TESTS PASSED ${NC}"
    echo -e "${GREEN}KETTER 3.0 IS FULLY OPERATIONAL AND PRODUCTION-READY${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    echo -e "\n${CYAN}System Components:${NC}"
    echo -e "   Docker Infrastructure:  ${GREEN}OPERATIONAL${NC}"
    echo -e "   PostgreSQL Database:    ${GREEN}OPERATIONAL${NC}"
    echo -e "   Redis Queue:            ${GREEN}OPERATIONAL${NC}"
    echo -e "   FastAPI Backend:        ${GREEN}OPERATIONAL${NC}"
    echo -e "   RQ Worker:              ${GREEN}OPERATIONAL${NC}"
    echo -e "   React Frontend:         ${GREEN}OPERATIONAL${NC}"
    echo -e "   Copy Engine:            ${GREEN}VERIFIED${NC}"
    echo -e "   Triple SHA-256:         ${GREEN}VERIFIED${NC}"
    echo -e "   PDF Reports:            ${GREEN}VERIFIED${NC}"
    echo -e "   Audit Trail:            ${GREEN}VERIFIED${NC}"

    echo -e "\n${CYAN}Access Points:${NC}"
    echo -e "  • Web UI:  ${YELLOW}http://localhost:3000${NC}"
    echo -e "  • API:     ${YELLOW}http://localhost:8000${NC}"
    echo -e "  • Docs:    ${YELLOW}http://localhost:8000/docs${NC}"

    echo -e "\n${GREEN} System ready for production use!${NC}\n"
    exit 0
else
    echo -e "\n${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED} SOME TESTS FAILED${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    echo -e "\n${RED}Failed Tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}${NC} $test"
    done

    echo -e "\n${YELLOW}Please review the errors above and fix them.${NC}\n"
    exit 1
fi
