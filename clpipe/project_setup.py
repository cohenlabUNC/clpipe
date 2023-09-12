import os, stat

import json
from pathlib import Path

from .utils import get_logger, add_file_handler
from .config.options import ProjectOptions

STEP_NAME = "project-setup"
DEFAULT_DICOM_DIR = 'data_DICOMs'
DCM2BIDS_SCAFFOLD_TEMPLATE = 'dcm2bids_scaffold -o {}'

DEFAULT_CONFIG_PATH = "data/defaultConvConfig.json"
DEFAULT_CONFIG_FILE_NAME = 'clpipe_config.json'

class SourceDataError(ValueError):
    pass

def project_setup(project_title: str="A Neuroimaging Project", project_dir: os.PathLike=os.getcwd(), 
                  source_data=None, move_source_data=False,
                  symlink_source_data=False, debug=False):
    """Initialize a clpipe project.

    No values can come in as None except source_data.

    Args documented in corresponding CLI function.

    Raises:
        SourceDataError: Invalid source data was provided.
        NotImplementedError: Option requested is not implemented.
    """
    logger = get_logger(STEP_NAME, debug=debug)

    default_dicom_dir = os.path.join(project_dir, DEFAULT_DICOM_DIR)
    
    if symlink_source_data and move_source_data:
        raise SourceDataError("Cannot choose to both move and symlink the source data.")
    if symlink_source_data and not source_data:
        raise SourceDataError("A source data path is required when using a symlinked source.")
    elif move_source_data and not source_data:
        raise SourceDataError("A source data path is required when moving source data.")
    elif source_data:
        logger.info(f"Referencing source data: {source_data}")
        source_data = Path(source_data).resolve()
    else:
        logger.info(f"No source data specified. Defaulting to: {default_dicom_dir}")
        source_data = default_dicom_dir
        Path(source_data).mkdir(exist_ok=False)
    
    logger.info(f"Starting project setup with title: {project_title}")

    logger.info(f"Creating new clpipe project in directory: {project_dir}")

    config:ProjectOptions = ProjectOptions()
    config.project_setup(project_title, project_dir, source_data)

    setup_convert2bids_directories(config)
    #setup_bids_validation_directories(config)
    #setup_fmriprep_directories(config)
    #setup_roiextract_directories(config)
    #setup_glm_directories(config['ProjectDirectory'])

    add_file_handler(config.get_logs_dir())
    # Set permissions to clpipe.log file to allow for group write
    os.chmod(os.path.join(config.get_logs_dir(), "clpipe.log"), 
             stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP)

    if symlink_source_data:
        logger.info(f'Creating SymLink for source data to {default_dicom_dir}')
        os.symlink(
            source_data,
            default_dicom_dir
        )
    elif move_source_data:
        raise NotImplementedError("Option -move_source_data is not yet implemented.")
    
    # Create an empty BIDS directory
    os.system(DCM2BIDS_SCAFFOLD_TEMPLATE.format(config.convert2bids.bids_directory))
    logger.debug(f"Created empty BIDS directory at: {config.convert2bids.bids_directory}")

    logger.debug('Creating JSON config file')

    config.dump(os.path.join(project_dir, DEFAULT_CONFIG_FILE_NAME))

    analyses_dir = os.path.join(project_dir, 'analyses')
    os.makedirs(analyses_dir, exist_ok=True)
    logger.debug(f'Created empty analyses directory: {analyses_dir}')

    script_dir = os.path.join(project_dir, 'scripts')
    os.makedirs(script_dir, exist_ok=True)
    logger.debug(f'Created empty scripts directory: {script_dir}')

    logger.info('Completed project setup')


def setup_convert2bids_directories(config):
    from pkg_resources import resource_stream

    # Create the step's core directories
    os.makedirs(config.convert2bids.bids_directory, exist_ok=True)
    os.makedirs(config.convert2bids.log_directory, exist_ok=True)

    # Create the default conversion config file
    if not os.path.exists(config.convert2bids.conversion_config):
        with resource_stream(__name__, DEFAULT_CONFIG_PATH) as def_conv_config:
            conv_config = json.load(def_conv_config)
        
        with open(config.convert2bids.conversion_config, 'w') as fp:
            json.dump(conv_config, fp, indent='\t')
        
    # Create a default .bidsignore file
    bids_ignore_path = os.path.join(config.convert2bids.bids_directory, ".bidsignore")
    if not os.path.exists(bids_ignore_path):
        with open(bids_ignore_path, 'w') as bids_ignore_file:
            # Ignore dcm2bid's auto-generated directory
            bids_ignore_file.write("tmp_dcm2bids\n")
            # Ignore heudiconv's auto-generated scan file
            bids_ignore_file.write("scans.json\n")


def setup_bids_validation_directories(config: ProjectOptions):
    os.makedirs(config.bids_validation.log_directory, exist_ok=True)


def setup_fmriprep_directories(config: ProjectOptions):
    os.makedirs(config.fmriprep.output_directory, exist_ok=True)
    os.makedirs(config.fmriprep.log_directory, exist_ok=True)


def setup_roiextract_directories(config: ProjectOptions):
    os.makedirs(config.roi_extraction.output_directory, exist_ok=True)
    os.makedirs(config.roi_extraction.log_directory, exist_ok=True)


def setup_glm_directories(project_path):
    os.mkdir(os.path.join(project_path, "l1_fsfs"))
    os.mkdir(os.path.join(project_path, "data_onsets"))
    os.mkdir(os.path.join(project_path, "l1_feat_folders"))
    os.mkdir(os.path.join(project_path, "l2_fsfs"))
    os.mkdir(os.path.join(project_path, "l2_gfeat_folders"))
    os.makedirs(os.path.join(project_path, "logs", "glm_logs", "L1_launch"))
    os.mkdir(os.path.join(project_path, "logs", "glm_logs", "L2_launch"))
