#!/bin/bash
# A simple script to build clpipe and generate the documentation
echo "Starting build"

echo "Clearing previous build"
rm -rf dist/*

# Build the .whl file
echo "Building wheel"
python -m build --wheel

# Build the documentation
echo "Building Documentation"
(cd docs; make html)

echo "Build complete"
