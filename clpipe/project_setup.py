import os, stat
from .config_json_parser import ClpipeConfigParser
from pkg_resources import resource_stream
import json
import sys
from pathlib import Path

from .config import DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_FILE_NAME
from .utils import get_logger, add_file_handler

STEP_NAME = "project-setup"
DEFAULT_DICOM_DIR = 'data_DICOMs'
DCM2BIDS_SCAFFOLD_TEMPLATE = 'dcm2bids_scaffold -o {}'

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

    add_file_handler(logs_dir)
    # Set permissions to clpipe.log file to allow for group write
    os.chmod(logs_dir / "clpipe.log", 
             stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP)

    config = config_parser.config

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
