#!/bin/bash
echo "Running post-link script for osdagbridge..."

PIP_EXE="$PREFIX/bin/python -m pip"

# Install pip-only dependencies
$PIP_EXE install --no-cache-dir openseespy>=3.2.2.6 opsvis

# # Save installed packages list
# $PREFIX/bin/python -m pip freeze > "$PREFIX/conda-meta/osdagbridge-pip.txt"

echo "Post-link completed."