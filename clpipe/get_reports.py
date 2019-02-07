import click
from .config_json_parser import ConfigParser
import os
import glob
import shutil
from distutils.dir_util import copy_tree, remove_tree
import sys
import logging
from .error_handler import exception_handler


@click.command()
@click.option('-configFile', type=click.Path(exists=True, dir_okay=False, file_okay=True), required = True, default = None)
@click.option('-outputName', default = 'Report_Archive')
@click.option('-debug', is_flag=True)
def get_reports(configfile, outputname, debug):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if configfile is None:
        raise ValueError('Please specify a configuration file.')

    config = ConfigParser()
    config.config_updater(configfile)


    fmriprepdir = config.config['FMRIPrepOptions']['OutputDirectory']

    image_dirs = [f.path for f in os.scandir(os.path.join(fmriprepdir, 'fmriprep')) if f.is_dir() ]

    for sub in [x for x in image_dirs if 'sub-' in x]:
        logging.info(sub)
        copy_tree(os.path.join(sub, 'figures'), os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'],'reports_temp', os.path.basename(sub), 'figures'))

    images = glob.glob(os.path.join(fmriprepdir, 'fmriprep', '*.html'))

    for report in images:
        logging.info(report)
        shutil.copy(report,
                        os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp', os.path.basename(report)))


    shutil.make_archive(base_name=outputname, root_dir = os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'],'reports_temp'), base_dir=os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'],'reports_temp'), format = 'zip')

    remove_tree( os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'],'reports_temp'))