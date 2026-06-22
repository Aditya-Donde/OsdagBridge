#!/bin/bash
echo "Running post-link script for osdagbridge..."

PIP_EXE="$PREFIX/bin/python -m pip"

$PIP_EXE install --upgrade pip || echo "pip upgrade skipped"

$PIP_EXE install --no-cache-dir "openseespy>=3.2.2.6" opsvis

if [ $? -ne 0 ]; then
    echo "WARNING: Optional pip dependencies failed."
    echo "Run manually: pip install openseespy opsvis"
    exit 0
fi

echo "Post-link completed."
exit 0