#!/bin/bash
# A simple script to build clpipe and generate the documentation

# Build the .whl file
python -m build --wheel

# Build the documentation
(cd docs; make html)

# Build bash auto-completion script
source generate_autocomplete
