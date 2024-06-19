# Setup modules needed for the development environment
# Specific to UNC Longleaf system but can be adapted to your system's available
#   modules.

# Clear any loaded modules
module purge

# Load all dependent modules

# Load system modules
module load fsl/6.0.3
module load freesurfer/6.0.0
module load afni/20.3.00
module load r/4.2.1
module load flywheel/16.4.0
module load dcm2niix/1.0.20211006 #Update to latest

# Load custom modules
module use /proj/hng/software/modules
module load flywheel/16.4.0
module load ants/2.3.1