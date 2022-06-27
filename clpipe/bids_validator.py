import os
import sys
import click
import logging
from .error_handler import exception_handler
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser


def bids_validate(bids_dir=None, config_file=None, log_dir=None, interactive=False, submit=True, verbose=False, debug=False):
    """Runs the BIDS-Validator program on a dataset. If a configuration file has a BIDSDirectory specified, you do not need to provide a BIDS directory in the command."""
    if not debug:
        sys.excepthook = exception_handler
    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.setup_bids_validation(log_dir)
    config.setup_fmriprep_directories(bids_dir, None, None)

    if bids_dir is None and config_file is None:
        raise ValueError('Specify a BIDS directory in either the configuration file, or in the command')

    batch_manager = BatchManager(batchsystemConfig=config.config['BatchConfig'], outputDirectory=config.config['BIDSValidationOptions']['LogDirectory'])
    batch_manager.update_mem_usage('3000')

    singularity_string = '''singularity run --cleanenv -B {bindPaths} {validatorInstance} {bidsDir}'''

    if verbose:
        singularity_string = singularity_string + ' --verbose'

    if interactive:
        os.system(singularity_string.format(
            validatorInstance=config.config['PostProcessingOptions']['BIDSValidatorImage'],
            bidsDir=config.config['FMRIPrepOptions']['BIDSDirectory'],
            bindPaths=batch_manager.config['SingularityBindPaths']
        ))
    else:
        batch_manager.addjob(Job("BIDSValidator", singularity_string.format(
            validatorInstance=config.config['PostProcessingOptions']['BIDSValidatorImage'],
            bidsDir=config.config['FMRIPrepOptions']['BIDSDirectory'],
            bindPaths=batch_manager.config['SingularityBindPaths']
        )))

        batch_manager.compilejobstrings()
        if submit:
            batch_manager.submit_jobs()
        else:
            batch_manager.print_jobs()
