#!/bin/bash

# Process cleanup function
cleanup_processes() {
    echo "Cleaning up existing backend processes..."
    
    # Kill processes by pattern (uvicorn and python running main.py)
    pkill -f "uvicorn.*src.main:app" 2>/dev/null || true
    pkill -f "python.*src.main" 2>/dev/null || true
    
    # Wait for processes to terminate
    sleep 2
    
    # Force kill if still running
    pkill -9 -f "uvicorn.*src.main:app" 2>/dev/null || true
    pkill -9 -f "python.*src.main" 2>/dev/null || true
    
    echo "Process cleanup complete"
}

# Perform cleanup
cleanup_processes

# Wait for port to be released
sleep 2

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to the backend directory
export PYTHONPATH="${SCRIPT_DIR}"

# Start the backend
cd "${SCRIPT_DIR}"
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
