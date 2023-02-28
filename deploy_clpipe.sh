# Deployment script
# UNC-specific but can be adapted for other clusters with a module system
# Run like this, where x.y.z is the version:
#   source deploy_clpipe.sh x.y.z

DEV_PYTHON_PATH="venv/bin/activate"
PYTHON_VERSION="3.7.14"
DEPLOY_ROOT="/proj/hng/software"
MODULE_ROOT="${DEPLOY_ROOT}/modules/clpipe"
VENVS="${DEPLOY_ROOT}/venvs/clpipe"

if [ $# -eq 0 ]
  then
    echo "1st argument required: version"
    exit 1
fi

version=$1

# Ensure dev env is loaded
source $DEV_PYTHON_PATH

# Run build script
source build_clpipe.sh

echo "Deploying version ${version}"
venv_path="${VENVS}/clpipe-${version}"
 
# Turn off dev virtual environment
deactivate

# Remove prior venv if needed
echo "Removing any prior virtual environment with same version"
rm -rf $venv_path

# Add a new venv for this release
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

# Build bash auto-completion script
echo "Building auto-completion bash script"
source generate_autocomplete

# Deploy auto-completion script
echo "Deploying auto-completion bash script"
cp dist/.clpipe-complete "${venv_path}/bin"

echo "Deployment complete"

# Turn off the deployment venv
deactivate

# Turn back on the dev venv
source $DEV_PYTHON_PATH

# Build the module file
python .lmod/build_module_file.py

# Deploy the module file
echo "Deploying module file"
cp "dist/${version}.lua" ${MODULE_ROOT}