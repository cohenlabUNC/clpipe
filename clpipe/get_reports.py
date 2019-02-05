import click
from .config_json_parser import ConfigParser
import os
import glob
import shutil
from distutils.dir_util import copy_tree

import logging

@click.command()
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True), required = True)
@click.option('-outputName', default = 'Report_Archive.zip')
def get_reports(configfile, outputname):
    logging.basicConfig(level=logging.DEBUG)
    config = ConfigParser()
    config.config_updater(configfile)


    fmriprepdir = config.config['FMRIPrepOptions']['OutputDirectory']

    image_dirs = [f.path for f in os.scandir(os.path.join(fmriprepdir, 'fmriprep')) if f.is_dir() ]

    for sub in [x for x in image_dirs if 'sub-' in x]:
        logging.info(sub)
        click.echo(copy_tree(os.path.join(sub, 'figures'), os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'],'reports_temp', os.path.basename(sub))))

    images = glob.glob(os.path.join(fmriprepdir, 'fmriprep', '*.html'))

    for report in images:
        logging.info(report)
        shutil.copy(report,
                        os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp', os.path.basename(report)))


    shutil.make_archive(base_name=outputname, root_dir = os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'],'reports_temp'), base_dir=os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'],'reports_temp'), format = 'zip')