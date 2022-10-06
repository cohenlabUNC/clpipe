#!/bin/bash
# A simple script to build clpipe and generate the documentation

python -m build --wheel
(cd docs; make html)