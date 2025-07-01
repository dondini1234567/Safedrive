#!/bin/bash
# Script to set up PyNTRU library

# Create a directory for external libraries
mkdir -p external_libs
cd external_libs

# Clone the PyNTRU repository
git clone https://github.com/smarky7CD/PyNTRU.git

# Install requirements for PyNTRU
pip install -r PyNTRU/requirements.txt

# Add the PyNTRU directory to PYTHONPATH in .env file
cd ..
echo "PYTHONPATH=\$PYTHONPATH:$(pwd)/external_libs" >> .env

echo "PyNTRU setup complete!"
