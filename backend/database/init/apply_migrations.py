#!/usr/bin/env python3
"""
Simple Database Migration Tool
Applies SQL migrations using Supabase REST API
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from config import settings


def execute_sql(sql: str) -> bool:
    """Execute SQL using Supabase REST API"""

    # Use Supabase's database REST API
    # This uses the PostgREST endpoint for raw SQL execution
    url = f"{settings.supabase_url}/rest/v1/rpc/exec_sql"

    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }

    # Note: Supabase doesn't allow arbitrary SQL execution via REST API
    # We need to use the SQL editor or psql for this
    print("WARNING: Supabase REST API doesn't support arbitrary SQL execution")
    print("        Using alternative approach with HTTP API...")

    # Alternative: Use Supabase Management API
    # This requires a different access token

    return False


def main():
    """Run all migrations"""

    print("\n" + "="*70)
    print("  Survey Sensei - Database Migration Tool")
    print("="*70 + "\n")

    migrations_dir = Path(__file__).parent.parent / "migrations"
    functions_dir = Path(__file__).parent.parent / "functions"

    if not migrations_dir.exists():
        print(f"ERROR: Migrations directory not found: {migrations_dir}")
        return 1

    # Get all SQL files from migrations directory (except the combined one)
    migration_files = sorted([
        f for f in migrations_dir.glob("*.sql")
        if f.name != "_combined_migrations.sql"
    ])

    # Get all SQL files from functions directory
    function_files = sorted(functions_dir.glob("*.sql")) if functions_dir.exists() else []

    # Combine migrations and functions (migrations first, then functions)
    sql_files = migration_files + function_files

    if not sql_files:
        print("WARNING: No migration or function files found")
        return 0

    print(f"Found {len(migration_files)} migration file(s) and {len(function_files)} function file(s):\n")

    print("Migrations:")
    for i, sql_file in enumerate(migration_files, 1):
        print(f"  {i}. {sql_file.name}")

    if function_files:
        print("\nFunctions:")
        for i, sql_file in enumerate(function_files, 1):
            print(f"  {i}. {sql_file.name}")

    print("\n" + "="*70)
    print("  Migration Contents")
    print("="*70 + "\n")

    all_sql = []

    for sql_file in sql_files:
        print(f"\n-- {sql_file.name} " + "-"*(65 - len(sql_file.name)))
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
            all_sql.append(content)

    print("\n" + "="*70)
    print("  How to Apply These Migrations")
    print("="*70 + "\n")

    project_ref = settings.supabase_url.split("//")[1].split(".")[0]

    print("Option 1: Supabase SQL Editor (Easiest)")
    print("-" * 70)
    print(f"1. Open: {settings.supabase_url}/project/default/sql/new")
    print("2. Copy ALL the SQL above (starting from the first migration)")
    print("3. Paste into SQL Editor and click 'Run'")

    print("\n\nOption 2: Using psql (Command Line)")
    print("-" * 70)
    print("1. Install PostgreSQL client: https://www.postgresql.org/download/")
    print("2. Get database password from Supabase Dashboard:")
    print(f"   {settings.supabase_url}/project/default/settings/database")
    print("\n3. Run migrations:\n")
    print("   On macOS/Linux:")
    print(f"   export PGPASSWORD='your-db-password'")
    print(f"   cat backend/database/migrations/*.sql | psql \\")
    print(f"       -h db.{project_ref}.supabase.co \\")
    print(f"       -p 5432 -U postgres -d postgres")
    print("\n   On Windows (PowerShell):")
    print(f"   $env:PGPASSWORD='your-db-password'")
    print(f"   Get-Content backend\\database\\migrations\\*.sql | psql `")
    print(f"       -h db.{project_ref}.supabase.co `")
    print(f"       -p 5432 -U postgres -d postgres")

    print("\n\nOption 3: Copy Combined SQL to Clipboard")
    print("-" * 70)

    combined_sql = "\n\n".join(all_sql)

    try:
        import pyperclip
        pyperclip.copy(combined_sql)
        print("SUCCESS: All SQL copied to clipboard!")
        print("        Paste directly into Supabase SQL Editor")
    except ImportError:
        print("TIP: Install pyperclip to auto-copy SQL:")
        print("     pip install pyperclip")

    print("\n" + "="*70 + "\n")

    # Save combined SQL to database root directory (not migrations subfolder)
    database_dir = migrations_dir.parent
    output_file = database_dir / "_combined_migrations.sql"

    # Add DROP statements at the beginning for master reset capability
    drop_statements = """-- ============================================================================
-- Survey Sensei - Master Reset Script
-- ============================================================================
-- This script drops all existing tables and recreates them from scratch
-- WARNING: This will DELETE ALL DATA in the database!
-- ============================================================================

-- Drop tables in reverse dependency order (drop dependent tables first)
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS survey_sessions CASCADE;
DROP TABLE IF EXISTS survey CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS match_products(vector, int, int) CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Note: Extensions are kept enabled (uuid-ossp, vector)
-- ============================================================================

"""

    # Combine: DROP statements + all migrations
    final_sql = drop_statements + combined_sql

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_sql)

    print(f"Combined SQL saved to: {output_file}")
    print(f"You can copy this entire file into Supabase SQL Editor")
    print(f"\nWARNING: This file includes DROP TABLE statements for master reset")
    print(f"         Running it will DELETE ALL DATA and recreate tables from scratch\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
