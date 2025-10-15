#!/bin/bash

# Kill any existing backend processes
pkill -f "python3 -m src.main" 2>/dev/null || true

# Wait for port to be released
sleep 2

# Set PYTHONPATH
export PYTHONPATH=/Users/andrewflick/Documents/SentimentAgent/backend

# Start the backend
cd /Users/andrewflick/Documents/SentimentAgent/backend
python3 -m src.main
