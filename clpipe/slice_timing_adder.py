import os
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser
import glob
import json


@click.command()
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None)
@click.option('-bidsDir', type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.option('-slicetype')
@click.option('-nslices')
def slice_time_adder(configfile = None,bidsdir = None, slicetype = None, nslices=None):
    config = ConfigParser()
    config.config_updater(configfile)
    config.setup_fmriprep_directories(bidsdir, None, None)

    jsons = glob.glob(os.path.join(bidsdir, '**', '*bold.json'), recursive=True)

    for json_file in jsons:

        with open(os.path.abspath(json_file), "r") as config_file:
            json_dict = json.load(config_file)

