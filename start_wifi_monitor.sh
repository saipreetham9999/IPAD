#!/bin/bash

# This script automates the setup and execution of the Wi-Fi Monitor application on Ubuntu.
# It will:
# 1. Update package lists.
# 2. Ensure fping is installed.
# 3. Create a Python virtual environment.
# 4. Install required Python libraries.
# 5. Run the main application.

# --- Step 1: Update System and Install fping ---
echo ">>> Updating system packages and installing fping..."
sudo apt-get update
sudo apt-get install -y fping

# Check if fping was installed successfully
if ! command -v fping &> /dev/null
then
    echo "!!! fping could not be installed. Please check for errors above. Aborting."
    exit 1
fi
echo ">>> fping is installed."

# --- Step 2: Set up Python Virtual Environment ---
VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo ">>> Creating Python virtual environment in '$VENV_DIR'..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "!!! Failed to create virtual environment. Please ensure python3-venv is installed."
        echo "!!! Try running: sudo apt-get install python3-venv"
        exit 1
    fi
else
    echo ">>> Virtual environment already exists."
fi

# --- Step 3: Install Python Dependencies ---
echo ">>> Activating virtual environment and installing libraries from requirements.txt..."
source $VENV_DIR/bin/activate
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "!!! Failed to install Python libraries. Please check for errors above. Aborting."
    exit 1
fi
echo ">>> Python libraries installed successfully."

# --- Step 4: Run the Application ---
echo ">>> Starting the Brain application (Lite Mode)..."
echo ">>> Press CTRL+C to stop the application."
python3 run.py

# Deactivate the virtual environment when the script is stopped
deactivate
echo ">>> Application stopped."
