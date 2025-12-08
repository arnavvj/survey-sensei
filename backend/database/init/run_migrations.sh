#!/bin/bash
# ============================================================================
# Survey Sensei - Database Migration Script
# ============================================================================
#
# This script runs all SQL migrations in order using psql
#
# Prerequisites:
# 1. Install PostgreSQL client tools (includes psql)
#    - macOS: brew install postgresql
#    - Ubuntu: sudo apt-get install postgresql-client
#    - Windows: Download from https://www.postgresql.org/download/windows/
#
# 2. Get your Supabase database password:
#    - Go to Supabase Dashboard → Settings → Database
#    - Copy the database password (NOT the service role key)
#
# Usage:
#   ./run_migrations.sh
#
# Or with password as environment variable:
#   PGPASSWORD='your-db-password' ./run_migrations.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MIGRATIONS_DIR="$SCRIPT_DIR/../migrations"

# Extract Supabase project ref from backend .env.local
BACKEND_ENV="$SCRIPT_DIR/../../backend/.env.local"

if [ ! -f "$BACKEND_ENV" ]; then
    echo -e "${RED}❌ Error: Backend .env.local not found${NC}"
    echo "   Expected location: $BACKEND_ENV"
    exit 1
fi

# Parse Supabase URL to get project reference
SUPABASE_URL=$(grep SUPABASE_URL "$BACKEND_ENV" | cut -d '=' -f2)
PROJECT_REF=$(echo "$SUPABASE_URL" | sed 's|https://||' | cut -d '.' -f1)

# Database connection details
DB_HOST="db.${PROJECT_REF}.supabase.co"
DB_PORT="5432"
DB_USER="postgres"
DB_NAME="postgres"

echo ""
echo "============================================================"
echo "  Survey Sensei - Database Migration Tool"
echo "============================================================"
echo ""
echo "Database: ${BLUE}${DB_HOST}${NC}"
echo "User:     ${BLUE}${DB_USER}${NC}"
echo ""

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ Error: psql not found${NC}"
    echo ""
    echo "Please install PostgreSQL client tools:"
    echo "  - macOS:   brew install postgresql"
    echo "  - Ubuntu:  sudo apt-get install postgresql-client"
    echo "  - Windows: https://www.postgresql.org/download/windows/"
    echo ""
    exit 1
fi

# Check if password is set
if [ -z "$PGPASSWORD" ]; then
    echo -e "${YELLOW}⚠️  Database password not set${NC}"
    echo ""
    echo "Please set your Supabase database password:"
    echo "  1. Go to: ${SUPABASE_URL}/project/default/settings/database"
    echo "  2. Copy your database password (NOT the service role key)"
    echo "  3. Run: export PGPASSWORD='your-database-password'"
    echo "  4. Then run this script again"
    echo ""
    echo "Or run in one command:"
    echo "  PGPASSWORD='your-password' $0"
    echo ""
    exit 1
fi

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo -e "${RED}❌ Error: Migrations directory not found${NC}"
    echo "   Expected: $MIGRATIONS_DIR"
    exit 1
fi

# Count migration files
MIGRATION_COUNT=$(ls -1 "$MIGRATIONS_DIR"/*.sql 2>/dev/null | wc -l)

if [ "$MIGRATION_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No migration files found in $MIGRATIONS_DIR${NC}"
    exit 0
fi

echo "Found ${GREEN}${MIGRATION_COUNT}${NC} migration file(s)"
echo ""
echo "============================================================"
echo "  Running Migrations"
echo "============================================================"
echo ""

# Run migrations in order
SUCCESS_COUNT=0

for migration_file in "$MIGRATIONS_DIR"/*.sql; do
    filename=$(basename "$migration_file")
    echo -e "${BLUE}📄 Running:${NC} $filename"

    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration_file" -v ON_ERROR_STOP=1 > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Success${NC}"
        ((SUCCESS_COUNT++))
    else
        echo -e "   ${RED}❌ Failed${NC}"
        echo ""
        echo "Error running migration: $filename"
        echo "Trying again with verbose output..."
        echo ""
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration_file" -v ON_ERROR_STOP=1
        exit 1
    fi
    echo ""
done

echo "============================================================"
echo -e "  ${GREEN}✅ Migration Complete!${NC}"
echo "============================================================"
echo ""
echo "Successfully ran ${GREEN}${SUCCESS_COUNT}${NC} of ${MIGRATION_COUNT} migrations"
echo ""
