#!/bin/bash
# A simple script to build clpipe and generate the documentation

cd clpipe
mkdir clpipe-build
cd clpipe-build
mkdir data_DICOMs
cd ..
python -c'from clpipe import project_setup;import os; project_setup.project_setup("clpipe",os.getcwd(),"/data_DICOMs")'
cd ..
python -m build --wheel
cd docs
make html