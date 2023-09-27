APPLICATION_NAME = "clpipe"

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
SETUP_COMMAND_NAME = "project_setup"
PROJECT_TITLE_HELP = "Choose a title for your project."
PROJECT_DIR_HELP = "Where the project will be located."
SOURCE_DATA_HELP = \
    "Where the raw data (usually DICOMs) are located."
MOVE_SOURCE_DATA_HELP = \
    "Move source data into project/data_DICOMs folder. USE WITH CAUTION."
SYM_LINK_HELP = \
    "Symlink the source data into project/data_dicoms. Usually safe to do."

# BIDS conversion help
CONVERSION_COMMAND_NAME = "convert2bids"
CONVERSION_CONFIG_HELP = (
    "A conversion definition file, either a dcm2bids conversion config .json "
    "file or a heudiconv heuristic .py file."
)
DICOM_DIR_HELP = "The folder where subject dicoms are located."
DICOM_DIR_FORMAT_HELP = (
    "Format string which specifies how subjects/sessions are organized within the "
    "dicom_dir. Example: {subject}_{session}. See "
    "https://clpipe.readthedocs.io/en/latest/bids_convert.html for more details."
)
BIDS_DIR_HELP = "The dicom info output file name."
OVERWRITE_HELP = "Overwrite existing BIDS data?"
SUBJECT_HELP = (
    "DEPRECATED: specify one subject to process - can give an "
    "arbitrary number of subjects as arguments now."
)
SESSION_HELP = (
    "Specify the session to convert. Available sessions determined by the {session} "
    "placeholder given by dicom_dir_format."
)
LONGITUDINAL_HELP = (
    "Convert all subjects/sessions into individual pseudo-subjects. "
    "Use if you do not want T1w averaged across sessions during FMRIprep"
)
MODE_HELP = (
    "Specify which converter to use."
)

# BIDS Validation Help
VALIDATOR_COMMAND_NAME = "bids_validate"
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


# GLM Help
L1_PREPARE_FSF_COMMAND_NAME = "l1_prepare_fsf"
L2_PREPARE_FSF_COMMAND_NAME = "l2_prepare_fsf"
APPLY_MUMFORD_COMMAND_NAME = "apply_mumford"
ONSET_EXTRACT_COMMAND_NAME = "fsl_onset_extract"
OUTLIERS_COMMAND_NAME = "report_outliers"

# GLM Prepare
GLM_PREPARE_COMMAND_NAME = "prepare"

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