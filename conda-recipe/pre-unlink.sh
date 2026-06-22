#!/bin/bash
echo "Running pre-unlink script for osdagbridge..."

"$PREFIX/bin/python" -m pip uninstall -y openseespy opsvis

if [ $? -ne 0 ]; then
    echo "WARNING: pip cleanup failed, continuing..."
    exit 0
fi

echo "Pre-unlink completed."
exit 0