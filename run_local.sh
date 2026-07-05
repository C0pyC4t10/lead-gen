#!/bin/bash
# Just run the local server on port 8800
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null
python3 server.py
