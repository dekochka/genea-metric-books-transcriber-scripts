#!/bin/bash
# Setup script to install dependencies and run tests

set -e  # Exit on error

echo "=========================================="
echo "Setting up test environment"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt --quiet

# Install test dependencies
echo "Installing test dependencies (pytest, pytest-mock)..."
pip install pytest pytest-mock pytest-cov --quiet

echo ""
echo "=========================================="
echo "Running tests"
echo "=========================================="

# Run tests with coverage
python3 -m pytest tests/ -v --cov=transcribe --cov-report=term --cov-report=html

echo ""
echo "=========================================="
echo "Test run complete!"
echo "Coverage report generated in htmlcov/index.html"
echo "=========================================="
