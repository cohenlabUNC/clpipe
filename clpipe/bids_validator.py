import os

import click

from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser

@click.command()
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None)
@click.argument('bidsDir', type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.option('-interactive/-batch', default = False )
@click.option('-submit/-save', default = False)
def bids_validate(bidsdir = None, configfile = None, interactive = False, submit = True):
    config = ConfigParser()
    config.config_updater(configfile)
    config.setup_fmriprep_directories(bidsdir, None, None)

    batch_manager = BatchManager(batchsystemConfig=config.config['BatchConfig'])
    batch_manager.update_mem_usage('3000')

    singularity_string = '''singularity run --cleanenv -B {bindPaths} {validatorInstance} {bidsDir}'''

    if(interactive):
        os.system(singularity_string.format(
            validatorInstance = config.config['PostProcessingOptions']['BIDSValidatorImage'],
            bidsDir = config.config['BIDSDirectory'],
            bindPaths = batch_manager.config['SingularityBindPaths']
        ))
    else:
        batch_manager.addjob(Job("BIDSValidator",singularity_string.format(
            validatorInstance = config.config['PostProcessingOptions']['BIDSValidatorImage'],
            bidsDir = config.config['BIDSDirectory'],
            bindPaths = batch_manager.config['SingularityBindPaths']
        )))

        batch_manager.compilejobstrings()
        if submit:
            batch_manager.submit_jobs()
        else:
            batch_manager.print_jobs()
