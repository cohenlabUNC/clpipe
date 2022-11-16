import os
import sys
import click

from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
from .utils import add_file_handler, get_logger
from .config import CONFIG_HELP, LOG_DIR_HELP, SUBMIT_HELP, \
    INTERACTIVE_HELP, DEBUG_HELP, CLICK_FILE_TYPE_EXISTS, CLICK_DIR_TYPE_EXISTS

COMMAND_NAME = "validate"
STEP_NAME = "bids-validation"
SINGULARITY_CMD_TEMPLATE = ('singularity run --cleanenv -B {bindPaths} '
                      '{validatorInstance} {bidsDir}')

VERBOSE_HELP = (
    "Creates verbose validator output. Use if you want to see ALL files "
    "with errors/warnings."
)


@click.command(COMMAND_NAME)
@click.option('-config_file', type=CLICK_FILE_TYPE_EXISTS, default=None, 
              help=CONFIG_HELP)
@click.argument('bids_dir', type=CLICK_DIR_TYPE_EXISTS, required=False)
@click.option('-log_dir', type=CLICK_FILE_TYPE_EXISTS, default=None,
              help=LOG_DIR_HELP)
@click.option('-verbose', is_flag=True, default=False,
              help=VERBOSE_HELP)
@click.option('-submit', is_flag=True, help=SUBMIT_HELP)
@click.option('-interactive', is_flag=True, default=False,
              help=INTERACTIVE_HELP)
@click.option('-debug', is_flag=True, help=DEBUG_HELP)
def bids_validate_cli(bids_dir, config_file, log_dir, interactive, submit,
                      verbose, debug):
    """Check that the given directory conforms to the BIDS standard"""

    bids_validate(
        bids_dir=bids_dir, config_file=config_file, log_dir=log_dir, 
        interactive=interactive, submit=submit, verbose=verbose, debug=debug)


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

    singularity_string = SINGULARITY_CMD_TEMPLATE
    if verbose:
        logger.debug("Verbose mode: on")
        singularity_string = singularity_string + ' --verbose'
    if interactive:
        logger.info("Running BIDS validation interactively.")
        os.system(singularity_string.format(
            validatorInstance=config
                .config['PostProcessingOptions']['BIDSValidatorImage'],
            bidsDir=bids_dir,
            bindPaths=batch_manager.config['SingularityBindPaths']
        ))
        logger.info("Validation complete.")
    else:
        batch_manager.addjob(Job("BIDSValidator", singularity_string.format(
            validatorInstance=config
                .config['PostProcessingOptions']['BIDSValidatorImage'],
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
