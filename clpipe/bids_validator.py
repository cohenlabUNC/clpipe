
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser


@click.command()
@click.argument('bidsDir', type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True))

def bids_validate(bidsdir, configfile=None):

    config = ConfigParser()
    config.config_updater(configfile)

    validator_img = config.config['ValidatorImagePath']

    batch_manager = BatchManager()

    singularity_string = '''singularity run --cleanenv -B /proj {validatorInstance} {bidsDir} {outputDir} participant''' \
                         '''--participant-label {participantLabels} -w {workingdir} --fs-license-file {fslicense} --nthreads                                 {threads}'''
