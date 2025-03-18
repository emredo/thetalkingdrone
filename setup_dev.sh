#!/bin/bash
# Script to set up and maintain the development environment

# Ensure pip-tools is installed
pip install pip-tools

# Update requirements files from .in files
echo "Updating requirements.txt from requirements.in..."
pip-compile requirements.in

echo "Updating requirements-dev.txt from requirements-dev.in..."
pip-compile requirements-dev.in

# Install dependencies
echo "Installing all dependencies..."
pip-sync requirements.txt requirements-dev.txt

# Install the package in development mode
echo "Installing package in development mode..."
pip install -e .

echo "Development environment ready!" 