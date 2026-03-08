#!/bin/bash

# This script automates the setup and execution of the Wi-Fi Monitor application on Ubuntu.
# It explicitly uses a virtual environment to avoid conflicts with the system's Python.

# --- Step 1: Update System and Install Prerequisites ---
echo ">>> Updating system packages and installing prerequisites (fping, python3-venv)..."
sudo apt-get update
sudo apt-get install -y fping python3-venv

# Check if fping was installed successfully
if ! command -v fping &> /dev/null
then
    echo "!!! fping could not be installed. Please check for errors above. Aborting."
    exit 1
fi
echo ">>> Prerequisites are installed."

# --- Step 2: Set up Python Virtual Environment ---
VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo ">>> Creating Python virtual environment in '$VENV_DIR'..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "!!! Failed to create virtual environment. Aborting."
        exit 1
    fi
else
    echo ">>> Virtual environment already exists."
fi

# --- Step 3: Install Python Dependencies using the venv's pip ---
# This is the key change: we call the pip executable directly from the venv.
# This completely avoids the "externally managed environment" error.
echo ">>> Installing libraries from requirements.txt into the virtual environment..."
$VENV_DIR/bin/pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "!!! Failed to install Python libraries. Please check for errors above. Aborting."
    exit 1
fi
echo ">>> Python libraries installed successfully."

# --- Step 4: Run the Application using the venv's python ---
# We also call the python executable directly from the venv.
echo ">>> Starting the Brain application (Lite Mode)..."
echo ">>> Press CTRL+C to stop the application."
$VENV_DIR/bin/python3 run.py

echo ">>> Application stopped."
