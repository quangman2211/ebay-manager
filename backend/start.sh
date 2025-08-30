#!/bin/bash
# Start script for eBay Manager Backend

echo "Setting up eBay Manager Backend..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python setup.py

# Run basic tests
echo "Running basic tests..."
python test_basic.py

echo "Starting FastAPI server..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000