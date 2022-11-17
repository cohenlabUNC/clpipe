import click

APPLICATION_NAME = "clpipe"

# Click path validation types
CLICK_FILE_TYPE = click.Path(dir_okay=False, file_okay=True)
CLICK_FILE_TYPE_EXISTS = click.Path(
    exists=True, dir_okay=False, file_okay=True)
CLICK_DIR_TYPE = click.Path(dir_okay=True, file_okay=False)
CLICK_DIR_TYPE_EXISTS = click.Path(exists=True, dir_okay=True, file_okay=False)
CLICK_DIR_TYPE_NOT_EXIST = click.Path(
    exists=False, dir_okay=True, file_okay=False)

# Default paths
DEFAULT_BATCH_CONFIG_PATH = "slurmUNCConfig.json"
DEFAULT_CONFIG_PATH = "data/defaultConvConfig.json"
DEFAULT_CONFIG_FILE_NAME = 'clpipe_config.json'

# Global use help messages
CONFIG_HELP = "The path to your clpipe configuration file."
LOG_DIR_HELP = "Where to put your HPC output files (such as SLURM output files)."
SUBMIT_HELP = "Flag to submit commands to the HPC."
DEBUG_HELP = "Flag to enable detailed error messages and traceback."
STATUS_CACHE_HELP = "Path to a status cache file for pipeline automation."
INTERACTIVE_HELP = (
    "Run in interactive mode. Only use in an interactive "
    "compute session."
)
VERSION_HELP = "Display clpipe's version."
BATCH_HELP = 'Flag to create batch jobs without prompting.'
WORKING_DIR_HELP = (
    "Where to generate the working directory."
)
GLM_CONFIG_HELP = 'The path to your GLM configuration file.'

# Project setup help
SETUP_COMMAND_NAME = "setup"
PROJECT_DIR_HELP = "Where the project will be located."
SOURCE_DATA_HELP = \
    "Where the raw data (usually DICOMs) are located."
MOVE_SOURCE_DATA_HELP = \
    "Move source data into project/data_DICOMs folder. USE WITH CAUTION."
SYM_LINK_HELP = \
    "Symlink the source data into project/data_dicoms. Usually safe to do."

# BIDS conversion help
CONVERSION_COMMAND_NAME = "convert"
CONVERSION_CONFIG_HELP = (
    "A conversion definition file, either a dcm2bids conversion config .json "
    "file or a heudiconv heuristic .py file."
)
DICOM_DIR_HELP = "The folder where subject dicoms are located."
DICOM_DIR_FORMAT_HELP = (
    "Format string for how subjects/sessions are organized within the "
    "dicom_dir."
)
BIDS_DIR_HELP = "The dicom info output file name."
OVERWRITE_HELP = "Overwrite existing BIDS data?"
SUBJECT_HELP = (
    "DEPRECATED: specify one subject to process - can give an "
    "arbitrary number of subjects as arguments now."
)
SESSION_HELP = (
    "Specify the session to convert."
)
LONGITUDINAL_HELP = (
    "Convert all subjects/sessions into individual pseudo-subjects. "
    "Use if you do not want T1w averaged across sessions during FMRIprep"
)
MODE_HELP = (
    "Specify which converter to use."
)

# BIDS Validation Help
VALIDATOR_COMMAND_NAME = "validate"
VERBOSE_HELP = (
    "Creates verbose validator output. Use if you want to see ALL files "
    "with errors/warnings."
)

# FMRIPrep help
FMRIPREP_COMMAND_NAME = "preprocess"
FMRIPREP_BIDS_DIR_HELP = (
    "Which BIDS directory to process. If a configuration file is provided "
    "with a BIDS directory, this argument is not necessary."
)
FMRIPREP_OUTPUT_DIR_HELP = (
    "Where to put the preprocessed data. If a configuration file is provided "
    "with a output directory, this argument is not necessary."
)

# Postprocess help
POSTPROCESS_COMMAND_NAME = "postprocess"

# Postprocess2 help
POSTPROCESS2_COMMAND_NAME = "postprocess2"
FMRIPREP_DIR_HELP = (
    "Which fmriprep directory to process. "
    "If a configuration file is provided with a BIDS directory, " 
    "this argument is not necessary. Note, must point to the ``fmriprep`` "
    "directory, not its parent directory."
)
OUTPUT_DIR_HELP = (
    "Where to put the postprocessed data. If a configuration file is "
    "provided with a output directory, this argument is not necessary."
)
PROCESSING_STREAM_HELP = \
    "Specify a processing stream to use defined in your configuration file."
INDEX_HELP = 'Give the path to an existing pybids index database.'
REFRESH_INDEX_HELP = \
    'Refresh the pybids index database to reflect new fmriprep artifacts.'
DEFAULT_PROCESSING_STREAM_NAME = "smooth-filter-normalize"

# GLM Help
GLM_SETUP_COMMAND_NAME = "setup"
L1_PREPARE_FSF_COMMAND_NAME = "l1_prepare_fsf"
L2_PREPARE_FSF_COMMAND_NAME = "l2_prepare_fsf"
APPLY_MUMFORD_COMMAND_NAME = "apply_mumford"
ONSET_EXTRACT_COMMAND_NAME = "fsl_onset_extract"
OUTLIERS_COMMAND_NAME = "report_outliers"

# GLM Launch Help
GLM_LAUNCH_COMMAND_NAME = "launch"
L1_MODEL_HELP = 'Name of your L1 model'
L2_MODEL_HELP = 'Name of your L2 model'
LEVEL_HELP = "Level of your model, L1 or L2"
MODEL_HELP = 'Name of your model'
TEST_ONE_HELP = 'Only submit one job for testing purposes.'

# Other Help
STATUS_COMMAND_NAME = "status"
CACHE_FILE_HELP = "Path to your status cache file."