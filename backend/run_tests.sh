#!/bin/bash
# Survey Sensei Backend - Test Runner Script (Linux/Mac)

set -e  # Exit on error

echo "🧪 Survey Sensei Backend Test Suite"
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt
pip install -q pytest pytest-asyncio pytest-cov pytest-mock faker

# Parse command line arguments
RUN_INTEGRATION=false
COVERAGE=true
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --integration)
            RUN_INTEGRATION=true
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--integration] [--no-coverage] [--verbose]"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
fi

if [ "$RUN_INTEGRATION" = true ]; then
    echo -e "${YELLOW}⚠️  Running integration tests (requires OpenAI API key)${NC}"
    PYTEST_CMD="$PYTEST_CMD --run-integration"
else
    echo "ℹ️  Skipping integration tests (use --integration to enable)"
fi

if [ "$COVERAGE" = false ]; then
    PYTEST_CMD="$PYTEST_CMD --no-cov"
fi

# Run tests
echo ""
echo "🔬 Running tests..."
echo ""

$PYTEST_CMD

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""

    if [ "$COVERAGE" = true ]; then
        echo "📊 Coverage report generated: htmlcov/index.html"
        echo "   Open in browser: file://$(pwd)/htmlcov/index.html"
    fi
else
    echo ""
    echo -e "${YELLOW}❌ Some tests failed${NC}"
    exit 1
fi
