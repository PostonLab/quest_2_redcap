#!/bin/bash
# Setup script for Quest Labs → REDCap Converter

echo "Setting up environment..."

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "Virtual environment created in ./venv"
fi

# Activate venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete."
echo
echo "To run the script:"
echo "source venv/bin/activate"
echo "python process_labs.py INPUT_FILE OUTPUT_FILE [--lookup_file LOOKUP_FILE]"
