#!/bin/bash
# Azure Setup Script
# This script installs required Python packages for Azure development
# and initiates Azure CLI login

echo "Starting Azure setup process..."

set PYTHONPATH=C:\Users\Neil\Documents\GitHub

# Install required Python packages
echo "Installing Python packages..."
# Try to determine the correct Python command
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python and make sure it's in your PATH."
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"

# Check if pip is installed and install it if necessary
if ! $PYTHON_CMD -c "import pip" &>/dev/null; then
    echo "pip not found. Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $PYTHON_CMD get-pip.py
    rm get-pip.py
fi

# Now we can use pip
PIP_CMD="$PYTHON_CMD -m pip"
echo "Using pip command: $PIP_CMD"

# Install required Python packages
echo "Installing Python packages..."
$PIP_CMD install azure.identity
$PIP_CMD install semantic_kernel
$PIP_CMD install azure.ai.projects==1.0.0b10
$PIP_CMD install matplotlib

# Log in to Azure
echo "Initiating Azure login..."
az login

echo "Setup complete!"