import os, stat
from .config_json_parser import ClpipeConfigParser
from pkg_resources import resource_stream
import json
from pathlib import Path

from .utils import get_logger, add_file_handler

STEP_NAME = "project-setup"
DEFAULT_DICOM_DIR = 'data_DICOMs'
DCM2BIDS_SCAFFOLD_TEMPLATE = 'dcm2bids_scaffold -o {}'

DEFAULT_CONFIG_PATH = "data/defaultConvConfig.json"
DEFAULT_CONFIG_FILE_NAME = 'clpipe_config.json'

class SourceDataError(ValueError):
    pass

def project_setup(project_title=None, project_dir=None, 
                  source_data=None, move_source_data=False,
                  symlink_source_data=False, debug=False):

    config_parser = ClpipeConfigParser()

    project_dir = Path(project_dir).resolve()
    logs_dir = project_dir / "logs"

    logger = get_logger(STEP_NAME, debug=debug)

    default_dicom_dir = project_dir / DEFAULT_DICOM_DIR
    
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
        source_data.mkdir(exist_ok=False)
    
    logger.info(f"Starting project setup with title: {project_title}")

    logger.info(f"Creating new clpipe project in directory: {str(project_dir)}")
    config_parser.setup_project(project_title, str(project_dir), source_data)
    config = config_parser.config

    setup_dcm2bids_directories(config)
    setup_bids_validation_directories(config)
    setup_fmriprep_directories(config)
    setup_postproc(config)
    setup_postproc(config, beta_series=True)
    setup_roiextract_directories(config)
    setup_glm_directories(config['ProjectDirectory'])

    add_file_handler(logs_dir)
    # Set permissions to clpipe.log file to allow for group write
    os.chmod(logs_dir / "clpipe.log", 
             stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP)

    bids_dir = config['DICOMToBIDSOptions']['BIDSDirectory']
    conv_config_path = config['DICOMToBIDSOptions']['ConversionConfig']

    if symlink_source_data:
        logger.info(f'Creating SymLink for source data to {default_dicom_dir}')
        os.symlink(
            source_data,
            default_dicom_dir
        )
    elif move_source_data:
        raise NotImplementedError("Option -move_source_data is not yet implemented.")
    
    # Create an empty BIDS directory
    os.system(DCM2BIDS_SCAFFOLD_TEMPLATE.format(bids_dir))
    logger.debug(f"Created empty BIDS directory at: {bids_dir}")

    logger.debug('Creating JSON config file')

    config_parser.config_json_dump(str(project_dir), DEFAULT_CONFIG_FILE_NAME)

    with resource_stream(__name__, DEFAULT_CONFIG_PATH) as def_conv_config:
        conv_config = json.load(def_conv_config)
        logger.debug('Default conversion config loaded')

    with open(conv_config_path, 'w') as fp:
        json.dump(conv_config, fp, indent='\t')
        logger.debug(f'Created default conversion config file: {conv_config_path}')

    analyses_dir = project_dir / 'analyses'
    analyses_dir.mkdir(exist_ok=True)
    logger.debug(f'Created empty analyses directory: {analyses_dir}')

    script_dir = project_dir / 'scripts'
    script_dir.mkdir(exist_ok=True)
    logger.debug(f'Created empty scripts directory: {script_dir}')

    logger.info('Completed project setup')

def setup_dcm2bids_directories(config):
    if(config['DICOMToBIDSOptions']['BIDSDirectory'] != ""):
        os.makedirs(config['DICOMToBIDSOptions']['BIDSDirectory'], exist_ok=True)
    os.makedirs(config['DICOMToBIDSOptions']['LogDirectory'], exist_ok=True)

    # Create a default .bidsignore file
    bids_ignore_path = os.path.join(config['DICOMToBIDSOptions']['BIDSDirectory'], ".bidsignore")
    if not os.path.exists(bids_ignore_path):
        with open(bids_ignore_path, 'w') as bids_ignore_file:
            # Ignore dcm2bid's auto-generated directory
            bids_ignore_file.write("tmp_dcm2bids\n")
            # Ignore heudiconv's auto-generated scan file
            bids_ignore_file.write("scans.json\n")

def setup_bids_validation_directories(config):
    os.makedirs(config['BIDSValidationOptions']['LogDirectory'], exist_ok=True)

def setup_fmriprep_directories(config):
    if not os.path.isdir(config['FMRIPrepOptions']['BIDSDirectory']):
        raise ValueError('BIDS Directory does not exist')
    
    if(config['FMRIPrepOptions']['WorkingDirectory'] != "SET WORKING DIRECTORY"):
        os.makedirs(config['FMRIPrepOptions']['WorkingDirectory'], exist_ok=True)
    if(config['FMRIPrepOptions']['OutputDirectory'] != ""):
        os.makedirs(config['FMRIPrepOptions']['OutputDirectory'], exist_ok=True)
    if(config['FMRIPrepOptions']['LogDirectory'] != ""):
        os.makedirs(config['FMRIPrepOptions']['LogDirectory'], exist_ok=True)

def setup_postproc(config, beta_series=False):
    target_output = 'PostProcessingOptions'
    if beta_series:
        target_output = 'BetaSeriesOptions'

    if(config[target_output]['OutputDirectory'] != ""):
        os.makedirs(config[target_output]['OutputDirectory'], exist_ok=True)
    os.makedirs(config[target_output]['LogDirectory'], exist_ok=True)

def setup_roiextract_directories(config):
    if(config['ROIExtractionOptions']['OutputDirectory'] != ""):
        os.makedirs(config['ROIExtractionOptions']['OutputDirectory'], exist_ok=True)
    os.makedirs(config['ROIExtractionOptions']['LogDirectory'], exist_ok=True)

def setup_glm_directories(project_path):
    os.mkdir(os.path.join(project_path, "l1_fsfs"))
    os.mkdir(os.path.join(project_path, "data_onsets"))
    os.mkdir(os.path.join(project_path, "l1_feat_folders"))
    os.mkdir(os.path.join(project_path, "l2_fsfs"))
    os.mkdir(os.path.join(project_path, "l2_gfeat_folders"))
    os.makedirs(os.path.join(project_path, "logs", "glm_logs", "L1_launch"))
    os.mkdir(os.path.join(project_path, "logs", "glm_logs", "L2_launch"))
