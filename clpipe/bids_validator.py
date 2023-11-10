import os
import sys
from pathlib import Path

from .job_manager import JobManagerFactory
from .config.options import ProjectOptions
from .utils import get_logger

STEP_NAME = "bids-validation"
SINGULARITY_CMD_TEMPLATE = (
    "singularity run --cleanenv -B {bindPaths} " "{validatorInstance} {bidsDir}"
)
DEFAULT_MEMORY_USAGE = "3G"


def bids_validate(
    bids_dir=None,
    config_file=None,
    log_dir=None,
    interactive=False,
    submit=False,
    verbose=False,
    debug=False,
):
    """
    Runs the BIDS-Validator program on a dataset.
    If a configuration file has a BIDSDirectory specified,
    you do not need to provide a BIDS directory in the command.
    """
    config: ProjectOptions = ProjectOptions.load(config_file)
    config.bids_validation.load_cli_args(bids_directory=bids_dir, log_directory=log_dir)
    setup_dirs(config)

    logger = get_logger(STEP_NAME, debug=debug, log_dir=config.get_logs_dir())

    logger.info(f"Starting BIDS validation targeting: {bids_dir}")
    logger.debug(f"Using config file: {config_file}")

    if bids_dir is None and config_file is None:
        logger.error(
            (
                "Specify a BIDS directory in either the "
                "configuration file, or in the command"
            )
        )
        sys.exit(1)

    # batch_manager = BatchManager(
    #     config.batch_config_path, output_directory=log_dir, debug=debug
    # )
    # batch_manager.update_mem_usage(DEFAULT_MEMORY_USAGE)

    batch_manager = JobManagerFactory.get(
        batch_config=config.batch_config_path,
        output_directory=log_dir,
        debug=debug,
        mem_use=DEFAULT_MEMORY_USAGE
    )

    # Not sure what this is doing tbh
    config.bids_validation.bids_validator_image

    singularity_string = SINGULARITY_CMD_TEMPLATE
    if verbose:
        logger.debug("Verbose mode: on")
        singularity_string = singularity_string + " --verbose"
    if interactive:
        logger.info("Running BIDS validation interactively.")
        os.system(
            singularity_string.format(
                validatorInstance=config.bids_validation.bids_validator_image,
                bidsDir=bids_dir,
                bindPaths=batch_manager.config["SingularityBindPaths"],
            )
        )
        logger.info("Validation complete.")
    else:
        # batch_manager.addjob(
        #     Job(
        #         "BIDSValidator",
        #         singularity_string.format(
        #             validatorInstance=config.bids_validation.bids_validator_image,
        #             bidsDir=config.fmriprep.bids_directory,
        #             bindPaths=batch_manager.config["SingularityBindPaths"],
        #         ),
        #     )
        # )
        batch_manager.addjob(
                "BIDSValidator",
                singularity_string.format(
                    validatorInstance=config.bids_validation.bids_validator_image,
                    bidsDir=config.fmriprep.bids_directory,
                    bindPaths=batch_manager.config["SingularityBindPaths"],
                )
        )

        # batch_manager.compilejobstrings()
        if submit:
            logger.info("Running BIDS validation in batch mode.")
            batch_manager.submit_jobs()
            logger.info(f"Check {log_dir} for results.")
        else:
            batch_manager.print_jobs()


def setup_dirs(config: ProjectOptions):
    os.makedirs(config.bids_validation.log_directory, exist_ok=True)
