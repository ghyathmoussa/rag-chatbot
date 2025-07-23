#!/bin/bash

# Install dependencies if not already installed
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run tests
echo "Running tests..."
python3 -m pytest -v

# Run with coverage report
echo "Running tests with coverage..."
python3 -m pytest --cov=src --cov-report=html --cov-report=term