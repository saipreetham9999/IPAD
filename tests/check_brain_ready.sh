#!/bin/bash

# Brain readiness checker — verifies machine is ready for integration tests
# Usage:
#   ./tests/check_brain_ready.sh                  (local, port 8080)
#   ./tests/check_brain_ready.sh 192.168.1.100    (remote IP)
#   ./tests/check_brain_ready.sh 192.168.1.100:9000  (remote with custom port)

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
if [ $# -eq 0 ]; then
    BRAIN_URL="http://localhost:8080"
else
    # Handle IP or IP:PORT
    if [[ $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        BRAIN_URL="http://$1:8080"
    elif [[ $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$ ]]; then
        BRAIN_URL="http://$1"
    else
        BRAIN_URL="$1"
    fi
fi

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Brain Network Readiness Check${NC}"
echo -e "${CYAN}  Target: $BRAIN_URL${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

FAILED=0

# Check 1: Brain is reachable
echo -n "Checking if Brain is reachable... "
if timeout 5 curl -s "$BRAIN_URL/" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo -e "  ${RED}Brain not responding at $BRAIN_URL${NC}"
    echo -e "  ${YELLOW}Make sure Brain is running:${NC}"
    echo -e "    python run.py${NC}"
    echo -e "    or${NC}"
    echo -e "    python supervisor.py${NC}"
    FAILED=$((FAILED + 1))
fi

# Check 2: Brain reports online
echo -n "Checking if Brain reports online... "
BRAIN_STATUS=$(curl -s "$BRAIN_URL/" | grep -o '"brain":"online"' || echo "")
if [ ! -z "$BRAIN_STATUS" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo -e "  ${RED}Brain not reporting online status${NC}"
    FAILED=$((FAILED + 1))
fi

# Check 3: /api/status endpoint
echo -n "Checking /api/status endpoint... "
if timeout 5 curl -s "$BRAIN_URL/api/status" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo -e "  ${RED}/api/status not responding${NC}"
    FAILED=$((FAILED + 1))
fi

# Check 4: /api/health endpoint
echo -n "Checking /api/health endpoint... "
HEALTH_RESPONSE=$(curl -s "$BRAIN_URL/api/health" 2>/dev/null || echo "")
if [[ $HEALTH_RESPONSE == *"status"* ]]; then
    HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✅ PASS${NC} (status: $HEALTH_STATUS)"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo -e "  ${RED}/api/health not responding correctly${NC}"
    FAILED=$((FAILED + 1))
fi

# Check 5: /api/connect endpoint (POST)
echo -n "Checking /api/connect endpoint... "
CONNECT_TEST=$(curl -s -X POST "$BRAIN_URL/api/connect" \
    -H "Content-Type: application/json" \
    -d "{\"device_name\":\"test_readiness_check\",\"device_type\":\"test\"}" 2>/dev/null || echo "")
if [[ $CONNECT_TEST == *"status"* ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
    # Cleanup
    curl -s -X POST "$BRAIN_URL/api/disconnect" \
        -H "Content-Type: application/json" \
        -d "{\"device_name\":\"test_readiness_check\"}" > /dev/null 2>&1
else
    echo -e "${RED}❌ FAIL${NC}"
    echo -e "  ${RED}/api/connect not responding correctly${NC}"
    FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Brain is ready for testing.${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  1. Run standalone tests:"
    echo -e "     ${CYAN}python tests/test_brain_standalone.py $BRAIN_URL${NC}"
    echo -e "  2. Or run pytest:"
    echo -e "     ${CYAN}pytest tests/test_integration_endpoints.py -v --brain-url $BRAIN_URL${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED check(s) failed.${NC}"
    echo -e "${YELLOW}Cannot proceed with testing.${NC}"
    exit 1
fi
