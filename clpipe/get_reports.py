import click
from .config_json_parser import ConfigParser
import pandas as pd
import os
import glob
import shutil
import logging

@click.command()
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True), required = True)
@click.option('-outputName', default = 'Report_Archive.zip')
def get_reports(configfile, outputname):
    config = ConfigParser()
    config.config_updater(configfile)


    fmriprepdir = config.config['FMRIPrepOptions']['OutputDirectory']

    image_dirs = os.listdir(os.path.join(fmriprepdir, 'fmriprep'))

    for sub in [x for x in image_dirs if 'subject-' in x]:
        logging.info(sub)
        shutil.copytree(os.path.join(sub, 'figures'), os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'],'reports_temp', sub))

    images = glob.glob(os.path.join(fmriprepdir, 'fmriprep', '*.html'))

    for report in images:
        logging.info(report)
        shutil.copy(report,
                        os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp'))


    shutil.make_archive(base_name=outputname, root_dir = os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'],'reports_temp'), base_dir=os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'],'reports_temp'), format = 'zip')