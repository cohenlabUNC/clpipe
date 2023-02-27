# Deployment script
# UNC-specific but can be adapted for other clusters with a module system

PYTHON_VERSION="3.7.14"
PYTHON_PATH="/nas/longleaf/rhel8/apps/python/${PYTHON_VERSION}/bin/python"
DEPLOY_ROOT="/proj/hng/software"
VENVS="${DEPLOY_ROOT}/venvs/clpipe"

if [ $# -eq 0 ]
  then
    echo "1st argument required: version"
    exit 1
fi

version=$1
patch=$2

# Run build script
source build_clpipe.sh

# Turn off your virtual environment
deactivate

echo "Deploying version ${version}"
venv_path="${VENVS}/clpipe-${version}"

# Remove prior venv
echo "Removing any prior virtual environment with same version"
rm -rf $venv_path

# Add a module for clpipe
module purge
module add "python/${PYTHON_VERSION}"
echo "Creating virtual environment at: ${venv_path}"
python -m venv $venv_path
module purge

source "${venv_path}/bin/activate"

echo "Updating pip"
pip install -U pip

echo "Installing wheel"
pip install wheel

echo "Installing clpipe"
pip install "dist/clpipe-${version}-py3-none-any.whl"

echo "Deploying auto-completion bash script"
cp build/.clpipe-complete "${venv_path}/bin"

deactivate