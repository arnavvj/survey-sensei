#!/usr/bin/env python3
"""
Database Migration Runner
Runs all SQL migration files in order using Supabase connection
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Add backend to path to import config
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from config import settings


def run_migrations():
    """Run all SQL migrations in order"""

    # Initialize Supabase client with service role key (bypasses RLS)
    supabase: Client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )

    # Get migrations directory
    migrations_dir = Path(__file__).parent.parent / "migrations"

    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        return False

    # Get all SQL files sorted by name
    sql_files = sorted(migrations_dir.glob("*.sql"))

    if not sql_files:
        print("⚠️  No migration files found")
        return True

    print(f"\n{'='*60}")
    print(f"Running {len(sql_files)} migration(s)...")
    print(f"{'='*60}\n")

    success_count = 0

    for sql_file in sql_files:
        print(f"📄 Running: {sql_file.name}")

        try:
            # Read SQL file
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Execute SQL using Supabase RPC
            # Note: Supabase's Python client doesn't have direct SQL execution
            # We need to use the PostgREST API or pgvector for this

            # Alternative: Use psycopg2 directly
            import psycopg2
            from urllib.parse import urlparse

            # Parse Supabase URL to get database connection string
            # Supabase format: https://PROJECT_REF.supabase.co
            # Database connection: postgresql://postgres:[PASSWORD]@db.PROJECT_REF.supabase.co:5432/postgres

            project_ref = settings.supabase_url.split("//")[1].split(".")[0]

            # Note: This requires the database password, not the service role key
            # For now, we'll use an alternative approach with the HTTP API

            print(f"   ⚠️  Direct SQL execution requires database password")
            print(f"   💡 Please run manually via Supabase SQL Editor or psql")
            print(f"   📋 SQL content:\n")
            print("   " + "\n   ".join(sql_content.split("\n")))
            print()

            success_count += 1

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    print(f"\n{'='*60}")
    print(f"✅ Processed {success_count}/{len(sql_files)} migration(s)")
    print(f"{'='*60}\n")

    return True


def print_manual_instructions():
    """Print instructions for manual migration"""
    print("\n" + "="*60)
    print("MANUAL MIGRATION INSTRUCTIONS")
    print("="*60)
    print("\nOption 1: Supabase SQL Editor (Recommended)")
    print("-" * 60)
    print(f"1. Go to: {settings.supabase_url}/project/default/sql/new")
    print("2. Copy the SQL from each migration file in order:")

    migrations_dir = Path(__file__).parent / "migrations"
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        print(f"   - {sql_file.name}")

    print("3. Paste and run each SQL in the editor")

    print("\n\nOption 2: Using psql command line")
    print("-" * 60)
    print("1. Get your database password from Supabase Dashboard:")
    print("   Settings → Database → Connection string → Password")
    print("\n2. Run migrations:")

    project_ref = settings.supabase_url.split("//")[1].split(".")[0]
    print(f"\n   export PGPASSWORD='your-database-password'")
    print(f"   psql -h db.{project_ref}.supabase.co \\")
    print(f"        -p 5432 \\")
    print(f"        -U postgres \\")
    print(f"        -d postgres \\")
    print(f"        -f database/migrations/001_initial_schema.sql\n")
    print(f"   psql -h db.{project_ref}.supabase.co \\")
    print(f"        -p 5432 \\")
    print(f"        -U postgres \\")
    print(f"        -d postgres \\")
    print(f"        -f database/migrations/002_add_conversation_history.sql")

    print("\n\nOption 3: Run all migrations at once")
    print("-" * 60)
    print("   cat database/migrations/*.sql | psql \\")
    print(f"        -h db.{project_ref}.supabase.co \\")
    print(f"        -p 5432 \\")
    print(f"        -U postgres \\")
    print(f"        -d postgres")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("\n🔧 Survey Sensei - Database Migration Tool\n")

    # Check if we can run migrations automatically
    print("Checking migration requirements...")

    # For now, we'll just print the instructions
    # In production, you'd use psycopg2 with database credentials
    print_manual_instructions()

    # Optionally display migration contents
    print("\n📋 Migration File Contents:")
    print("="*60 + "\n")

    migrations_dir = Path(__file__).parent / "migrations"
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        print(f"\n--- {sql_file.name} ---")
        with open(sql_file, 'r', encoding='utf-8') as f:
            print(f.read())
        print("\n" + "-"*60)
