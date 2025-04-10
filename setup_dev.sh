#!/bin/bash
# Script to set up and maintain the development environment

# Ensure pip-tools is installed
pip install pip-tools

# Update requirements file from .in file
echo "Updating requirements.txt from requirements.in..."
pip-compile requirements.in

# Install dependencies
echo "Installing all dependencies..."
python -m pip install -r requirements.txt

echo "Development environment ready!" 