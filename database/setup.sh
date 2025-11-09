#!/bin/bash

# Survey Sensei - Database Setup Script
# Automates Supabase database initialization

set -e  # Exit on error

echo "=================================="
echo "Survey Sensei - Database Setup"
echo "=================================="
echo ""

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating from .env.example..."
    cp ../.env.example ../.env
    echo ""
    echo "❗ Please edit .env file with your actual credentials:"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_ANON_KEY"
    echo "   - SUPABASE_SERVICE_KEY"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Load environment variables
source ../.env

# Validate required variables
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo "❌ Missing required environment variables!"
    echo "   Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env"
    exit 1
fi

echo "✅ Environment variables loaded"
echo ""

# Extract database connection details from Supabase URL
PROJECT_REF=$(echo $SUPABASE_URL | sed -E 's|https://([^.]+)\.supabase\.co|\1|')
DB_HOST="db.${PROJECT_REF}.supabase.co"
DB_PORT="5432"
DB_NAME="postgres"
DB_USER="postgres"

echo "📊 Database Connection Details:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo ""

# Check if psql is installed (optional - for direct DB access)
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client (psql) found"
    USE_PSQL=true
else
    echo "⚠️  psql not found - will use Supabase REST API"
    echo "   Install PostgreSQL client for faster setup"
    USE_PSQL=false
fi
echo ""

# Option 1: Use Supabase CLI (recommended)
if command -v supabase &> /dev/null; then
    echo "✅ Supabase CLI found"
    echo ""
    echo "🚀 Running migrations..."
    echo ""

    # Link to remote project
    echo "Linking to Supabase project..."
    supabase link --project-ref $PROJECT_REF

    # Run migrations
    echo "Executing schema migration..."
    supabase db push

    echo ""
    echo "✅ Migration completed!"

else
    echo "⚠️  Supabase CLI not found"
    echo ""
    echo "📥 Install Supabase CLI for easier management:"
    echo "   npm install -g supabase"
    echo "   or"
    echo "   brew install supabase/tap/supabase"
    echo ""
    echo "🔧 Manual Setup Required:"
    echo ""
    echo "1. Go to: $SUPABASE_URL/project/default/sql"
    echo "2. Copy contents of: migrations/001_initial_schema.sql"
    echo "3. Paste and execute in Supabase SQL Editor"
    echo "4. (Optional) Load sample data from: seed/001_sample_data.sql"
    echo ""
fi

# Verify setup
echo ""
echo "🔍 Verifying installation..."
echo ""

# Check if we can connect (using supabase CLI or curl)
VERIFY_URL="${SUPABASE_URL}/rest/v1/products?limit=1"

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "apikey: ${SUPABASE_ANON_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_ANON_KEY}" \
    "$VERIFY_URL")

if [ "$RESPONSE" == "200" ]; then
    echo "✅ Database connection verified!"
    echo "✅ Products table accessible"
else
    echo "⚠️  Could not verify database connection (HTTP $RESPONSE)"
    echo "   This might be normal if tables are empty"
fi

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "📚 Next Steps:"
echo ""
echo "1. Review database schema:"
echo "   cat database/README.md"
echo ""
echo "2. (Optional) Load sample data:"
echo "   Execute: database/seed/001_sample_data.sql"
echo "   in Supabase SQL Editor"
echo ""
echo "3. Test connection:"
echo "   Check tables in Supabase Dashboard → Table Editor"
echo ""
echo "4. Start Phase 1 (Frontend Development):"
echo "   Ready for UI implementation!"
echo ""
