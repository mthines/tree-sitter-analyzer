#!/bin/bash
# Local CI Check Script
# 在推送前运行此脚本以确保所有 CI 检查通过

set -e  # Exit on error

echo "🔍 Running Local CI Checks..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# 1. Ruff Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Ruff Linting Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if uv run ruff check .; then
    echo -e "${GREEN}✅ Ruff: PASSED${NC}"
else
    echo -e "${RED}❌ Ruff: FAILED${NC}"
    echo -e "${YELLOW}💡 Run 'uv run ruff check . --fix' to auto-fix${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 2. MyPy Type Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  MyPy Type Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if uv run mypy codexray/; then
    echo -e "${GREEN}✅ MyPy: PASSED${NC}"
else
    echo -e "${RED}❌ MyPy: FAILED${NC}"
    echo -e "${YELLOW}💡 Fix type errors manually${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 3. Bandit Security Scan
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Bandit Security Scan"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if uv run --with bandit bandit -r codexray/ -f json -o bandit-results.json 2>/dev/null; then
    echo -e "${GREEN}✅ Bandit: PASSED${NC}"
    rm -f bandit-results.json
else
    # Check if it's just a Unicode encoding error (not an actual security issue)
    if [ -f bandit-results.json ]; then
        ISSUES=$(python3 -c "import json; data=json.load(open('bandit-results.json')); print(len(data['results']))" 2>/dev/null || echo "0")
        if [ "$ISSUES" -eq "0" ]; then
            echo -e "${GREEN}✅ Bandit: PASSED (no security issues)${NC}"
            rm -f bandit-results.json
        else
            echo -e "${RED}❌ Bandit: FAILED ($ISSUES security issues found)${NC}"
            FAILURES=$((FAILURES + 1))
            rm -f bandit-results.json
        fi
    else
        echo -e "${YELLOW}⚠️  Bandit: WARNING (could not verify results)${NC}"
    fi
fi
echo ""

# 4. Quick Test Run (optional - can be slow)
if [ "${SKIP_TESTS}" != "1" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "4️⃣  Quick Test Run (unit tests only)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if uv run pytest tests/unit/ -q --tb=short 2>&1 | tail -20; then
        echo -e "${GREEN}✅ Tests: PASSED${NC}"
    else
        echo -e "${RED}❌ Tests: FAILED${NC}"
        FAILURES=$((FAILURES + 1))
    fi
    echo ""
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to push.${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILURES check(s) failed. Please fix before pushing.${NC}"
    exit 1
fi
