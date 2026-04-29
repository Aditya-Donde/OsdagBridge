#!/bin/bash
echo "Running pre-unlink script for osdagbridge..."

PIP_EXE="$PREFIX/bin/python -m pip"

$PIP_EXE uninstall -y openseespy opsvis

echo "Pre-unlink completed."