#!/bin/bash
cd "$(dirname "$0")"

# Ensure venv exists
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv backend/venv
fi

# Activate venv
source backend/venv/bin/activate

# Install dependencies if needed (quietly)
echo "Checking dependencies..."
pip install -q -r backend/requirements.txt

# Run server
echo "Starting Vocalize Backend..."
python3 backend/main.py
