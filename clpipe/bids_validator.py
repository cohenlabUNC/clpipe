import os
import sys

from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
from .utils import add_file_handler, get_logger

STEP_NAME = "bids-validation"
SINGULARITY_CMD_TEMPLATE = ('singularity run --cleanenv -B {bindPaths} '
                      '{validatorInstance} {bidsDir}')


def bids_validate(bids_dir=None, config_file=None, log_dir=None, 
                        interactive=False, submit=False, verbose=False, 
                        debug=False):
    """
    Runs the BIDS-Validator program on a dataset. 
    If a configuration file has a BIDSDirectory specified, 
    you do not need to provide a BIDS directory in the command.
    """
    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.setup_bids_validation(log_dir)
    config.setup_fmriprep_directories(bids_dir, None, None)

    bids_dir = config.config['FMRIPrepOptions']['BIDSDirectory']
    batch_config = config.config['BatchConfig']
    log_dir = config.config['BIDSValidationOptions']['LogDirectory']
    project_dir = config.config["ProjectDirectory"]

    add_file_handler(os.path.join(project_dir, "logs"))
    logger = get_logger(STEP_NAME, debug=debug)

    logger.info(f"Starting BIDS validation targeting: {bids_dir}")
    logger.debug(f"Using config file: {config_file}")

    if bids_dir is None and config_file is None:
        logger.error(('Specify a BIDS directory in either the '
                      'configuration file, or in the command'))
        sys.exit(1)
    
    batch_manager = BatchManager(
        batch_config, 
        output_directory=log_dir,
        debug=debug)
    batch_manager.update_mem_usage('3000')

    # Validator image moved to BIDSValidationOptions block
    # If the image isn't there, try looking in the old spot for backwards compatibility
    #   with clpipe <= v1.7.2
    try:
        bids_validator_image = config.config['BIDSValidationOptions']['BIDSValidatorImage']
    except KeyError:
        bids_validator_image = config.config['PostProcessingOptions']['BIDSValidatorImage']

    singularity_string = SINGULARITY_CMD_TEMPLATE
    if verbose:
        logger.debug("Verbose mode: on")
        singularity_string = singularity_string + ' --verbose'
    if interactive:
        logger.info("Running BIDS validation interactively.")
        os.system(singularity_string.format(
            validatorInstance=bids_validator_image,
            bidsDir=bids_dir,
            bindPaths=batch_manager.config['SingularityBindPaths']
        ))
        logger.info("Validation complete.")
    else:
        batch_manager.addjob(Job("BIDSValidator", singularity_string.format(
            validatorInstance=bids_validator_image,
            bidsDir=config.config['FMRIPrepOptions']['BIDSDirectory'],
            bindPaths=batch_manager.config['SingularityBindPaths']
        )))

        batch_manager.compilejobstrings()
        if submit:
            logger.info("Running BIDS validation in batch mode.")
            batch_manager.submit_jobs()
            logger.info(f"Check {log_dir} for results.")
        else:
            batch_manager.print_jobs()
