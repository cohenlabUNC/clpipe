import os

import click

from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser

@click.command()
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None)
@click.option('-bidsDir', type=click.Path(exists=True, dir_okay=True, file_okay=False))

def bids_validate(bidsdir = None, configfile = None):
    config = ConfigParser()
    config.config_updater(configfile)
    config.setup_directories(bidsdir, None, None)

    batch_manager = BatchManager(batchsystemConfig=config.config['BatchConfig'])
    batch_manager.update_mem_usage('3000')

    singularity_string = '''singularity run --cleanenv -B /proj {validatorInstance} {bidsDir}'''

    batch_manager.addjob(Job("BIDSValidator",singularity_string.format(
        validatorInstance = config.config['BIDSValidatorImage'],
        bidsDir = config.config['BIDSDirectory']
    )))

    batch_manager.compilejobstrings()
    batch_manager.submit_jobs()
    
