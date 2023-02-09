import os, stat
from .config_json_parser import ClpipeConfigParser
from pkg_resources import resource_stream
import json
import logging

from .config import DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_FILE_NAME
from .utils import get_logger, add_file_handler

STEP_NAME = "project-setup"
DEFAULT_DICOM_DIR = 'data_DICOMs'
DCM2BIDS_SCAFFOLD_TEMPLATE = 'dcm2bids_scaffold -o {}'


def project_setup(project_title=None, project_dir=None, 
                  source_data=None, move_source_data=None,
                  symlink_source_data=None, debug=False):

    config_parser = ClpipeConfigParser()
    org_source = os.path.abspath(source_data)

    add_file_handler(os.path.join(project_dir, "logs"))
    # Set permissions to clpipe.log file to allow for group write
    os.chmod(os.path.join(os.path.join(project_dir, "logs"), "clpipe.log"), 
             stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP)
    logger = get_logger(STEP_NAME, debug=debug)

    org_source = os.path.abspath(source_data)
    default_dicom_dir = os.path.join(os.path.abspath(project_dir), DEFAULT_DICOM_DIR)
    
    logger.info(f"Starting project setup with title: {project_title}")

    config_parser.setup_project(project_title, project_dir, source_data)

    config = config_parser.config

    # Create the project directory
    os.makedirs(project_dir, exist_ok=True)
    logger.info(f"Created project directory at: {project_dir}")

    bids_dir = config['DICOMToBIDSOptions']['BIDSDirectory']
    project_dir = config['ProjectDirectory']
    conv_config_path = config['DICOMToBIDSOptions']['ConversionConfig']

    if symlink_source_data:
        logger.info(f'Creating SymLink for source data to {default_dicom_dir}')
        os.symlink(
            os.path.abspath(org_source),
            default_dicom_dir
        )
    
    # Create an empty BIDS directory
    os.system(DCM2BIDS_SCAFFOLD_TEMPLATE.format(bids_dir))
    logger.debug(f"Created empty BIDS directory at: {bids_dir}")

    logger.debug('Creating JSON config file')

    config_parser.config_json_dump(project_dir, DEFAULT_CONFIG_FILE_NAME)

    with resource_stream(__name__, DEFAULT_CONFIG_PATH) as def_conv_config:
        conv_config = json.load(def_conv_config)
        logger.debug('JSON object loaded')

    with open(conv_config_path, 'w') as fp:
        json.dump(conv_config, fp, indent='\t')
        logger.debug('JSON indentation completed')

    os.makedirs(os.path.join(project_dir, 'analyses'), 
                exist_ok=True)
    logger.debug('Created empty analyses directory')

    os.makedirs(os.path.join(project_dir, 'scripts'), 
                exist_ok=True)
    logger.debug('Created empty scripts directory')

    logger.info('Completed project setup')