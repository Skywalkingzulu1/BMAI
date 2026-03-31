#!/usr/bin/env bash
# ------------------------------------------------------------
# Script to set up a Python virtual environment for the BMAI project
# ------------------------------------------------------------

# Exit on any error
set -e

# Define the virtual environment directory
VENV_DIR=".venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Activate the virtual environment
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Upgrade pip and install required packages
echo "Upgrading pip..."
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "No requirements.txt found. Skipping dependency installation."
fi

echo "Setup complete. To activate the virtual environment later, run:"
echo "source $VENV_DIR/bin/activate   # On Windows use $VENV_DIR\\Scripts\\activate"