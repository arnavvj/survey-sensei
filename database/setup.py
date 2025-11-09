#!/usr/bin/env python3
"""
Survey Sensei - Database Setup Script (Python version)
Provides cross-platform database initialization for Windows/Linux/Mac
"""

import os
import sys
from pathlib import Path
from typing import Optional
import json

try:
    import requests
except ImportError:
    print("❌ requests library not found!")
    print("   Install with: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("⚠️  python-dotenv not found (optional)")
    print("   Install with: pip install python-dotenv")
    load_dotenv = None


class SupabaseSetup:
    """Handles Supabase database setup and verification"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.db_dir = Path(__file__).parent
        self.env_file = self.project_root / ".env"

        # Load environment variables
        if load_dotenv:
            load_dotenv(self.env_file)

        self.supabase_url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")

    def print_header(self):
        """Print setup header"""
        print("=" * 50)
        print("Survey Sensei - Database Setup")
        print("=" * 50)
        print()

    def check_env_file(self) -> bool:
        """Check if .env file exists and has required variables"""
        if not self.env_file.exists():
            print("⚠️  .env file not found!")
            print("Creating from .env.example...")

            example_file = self.project_root / ".env.example"
            if example_file.exists():
                import shutil
                shutil.copy(example_file, self.env_file)
                print()
                print("❗ Please edit .env file with your actual credentials:")
                print("   - SUPABASE_URL")
                print("   - SUPABASE_ANON_KEY")
                print("   - SUPABASE_SERVICE_KEY")
                print()
                print("Then run this script again.")
                return False
            else:
                print("❌ .env.example not found!")
                return False

        if not self.supabase_url or not self.anon_key:
            print("❌ Missing required environment variables!")
            print("   Please set SUPABASE_URL and SUPABASE_ANON_KEY in .env")
            return False

        print("✅ Environment variables loaded")
        print()
        return True

    def read_sql_file(self, filename: str) -> str:
        """Read SQL file contents"""
        filepath = self.db_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"SQL file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def execute_sql_via_api(self, sql: str) -> bool:
        """Execute SQL using Supabase REST API (limited)"""
        print("⚠️  Direct SQL execution via REST API is limited")
        print("   Recommended: Use Supabase SQL Editor for schema migration")
        return False

    def verify_connection(self) -> bool:
        """Verify Supabase connection and table access"""
        print("🔍 Verifying database connection...")

        url = f"{self.supabase_url}/rest/v1/products"
        headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.anon_key}"
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                params={"limit": 1},
                timeout=10
            )

            if response.status_code == 200:
                print("✅ Database connection verified!")
                print("✅ Products table accessible")
                return True
            elif response.status_code == 404:
                print("⚠️  Tables not found (HTTP 404)")
                print("   Schema migration needed")
                return False
            else:
                print(f"⚠️  Unexpected response (HTTP {response.status_code})")
                print(f"   Response: {response.text[:200]}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False

    def print_manual_instructions(self):
        """Print manual setup instructions"""
        print()
        print("=" * 50)
        print("📋 Manual Setup Instructions")
        print("=" * 50)
        print()
        print("Since automated SQL execution is limited, please:")
        print()
        print(f"1. Open Supabase SQL Editor:")
        print(f"   {self.supabase_url}/project/default/sql")
        print()
        print("2. Enable required extensions:")
        print("   CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        print("   CREATE EXTENSION IF NOT EXISTS \"vector\";")
        print()
        print("3. Execute schema migration:")
        print(f"   Copy: {self.db_dir / 'migrations' / '001_initial_schema.sql'}")
        print("   Paste into SQL Editor and run")
        print()
        print("4. (Optional) Load sample data:")
        print(f"   Copy: {self.db_dir / 'seed' / '001_sample_data.sql'}")
        print("   Paste into SQL Editor and run")
        print()
        print("5. Verify setup:")
        print("   Run this script again to verify connection")
        print()

    def print_success(self):
        """Print success message"""
        print()
        print("=" * 50)
        print("✅ Setup Complete!")
        print("=" * 50)
        print()
        print("📚 Next Steps:")
        print()
        print("1. Review database schema:")
        print(f"   {self.db_dir / 'README.md'}")
        print()
        print("2. Check Supabase Dashboard:")
        print(f"   {self.supabase_url}/project/default/editor")
        print()
        print("3. Start Phase 1 (Frontend Development)")
        print()

    def run(self):
        """Run the setup process"""
        self.print_header()

        # Check environment
        if not self.check_env_file():
            sys.exit(1)

        # Print connection details
        print("📊 Database Connection Details:")
        print(f"   URL: {self.supabase_url}")
        print()

        # Verify connection
        if self.verify_connection():
            self.print_success()
        else:
            print()
            print("❌ Database not fully configured")
            self.print_manual_instructions()

        return 0


def main():
    """Main entry point"""
    setup = SupabaseSetup()
    return setup.run()


if __name__ == "__main__":
    sys.exit(main())
