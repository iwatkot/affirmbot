#!/bin/bash

# Checking if .venv dir already exists.
if [ -d ".venv" ]; then
    echo "VENV dir (.venv) already exists, it will be removed."
    rm -rf .venv
fi

echo "VENV will be created"

# Checking if python3.9 is available in PATH.
if command -v python3.9 &>/dev/null; then
    python_executable="python3.9" && \
    echo "Python 3.9 found, it will be used for creating VENV dir."
else
    python_executable="python3" && \
    echo "Python 3.9 not found, default python3 will be used for creating VENV dir."
fi

# Creating VENV dir with selected python executable.
$python_executable -m venv .venv && \
source .venv/bin/activate && \

# Installing requirements from requirements.txt.
echo "Install dev_requirements..." && \
pip3 install -r dev_requirements.txt && \
echo "Requirements have been successfully installed, VENV ready." && \
deactivate
