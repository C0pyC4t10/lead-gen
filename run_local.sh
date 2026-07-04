#!/bin/bash
# Setup script for running the lead-gen server locally
# This connects to the same Supabase DB as the deployed webapp

set -e

cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Install Python 3.11+"
    exit 1
fi

# Create venv if not exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Install deps
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Install Playwright browser (one-time, ~150MB)
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "Installing Playwright Chromium browser..."
    python3 -m playwright install chromium
fi

# Set DATABASE_URL to Supabase (so local + deployed share data)
export DATABASE_URL="postgresql://postgres:Jahid.Skarbol%4017@db.lkmgyvkqbdftpgyvpcrd.supabase.co:5432/postgres"

# Load .env if exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Verify Supabase connection
echo ""
echo "=== Verifying Supabase connection... ==="
python3 -c "
import os
os.environ['DATABASE_URL'] = '$DATABASE_URL'
try:
    import psycopg2
    conn = psycopg2.connect('$DATABASE_URL', connect_timeout=10)
    print('  ✅ Connected to Supabase')
    conn.close()
except Exception as e:
    print(f'  ❌ Connection failed: {e}')
    print('  If you see Network is unreachable, your ISP blocks Supabase IP.')
    print('  Try a different network or use VPN.')
    exit 1
"

echo ""
echo "=== Starting server on http://localhost:8800 ==="
echo "Your webapp at https://scraven.vercel.app will show leads saved here."
echo "Press Ctrl+C to stop."
echo ""

python3 server.py
