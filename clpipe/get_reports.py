from .config_json_parser import ClpipeConfigParser
import os
import glob
import shutil
from distutils.dir_util import copy_tree, remove_tree
import sys
import logging
from .error_handler import exception_handler


def get_reports(config_file, output_name, debug):
    """This command creates a zip archive of fmriprep QC reports for download."""
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if config_file is None:
        raise ValueError('Please specify a configuration file.')

    config = ClpipeConfigParser()
    config.config_updater(config_file)

    fmriprepdir = config.config['FMRIPrepOptions']['OutputDirectory']

    image_dirs = [f.path for f in os.scandir(os.path.join(fmriprepdir, 'fmriprep')) if f.is_dir()]

    for sub in [x for x in image_dirs if 'sub-' in x]:
        logging.info(sub)
        copy_tree(os.path.join(sub, 'figures'),
                  os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp',
                               os.path.basename(sub), 'figures'))
        ses_dirs = [f.path for f in os.scandir(sub) if f.is_dir()]
        for ses in [x for x in ses_dirs if 'ses-' in x]:
            if os.path.isdir(os.path.join(ses, 'figures')):
                   copy_tree(os.path.join(ses, 'figures'),
                        os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp',
                                   os.path.basename(sub),os.path.basename(ses), 'figures'))
    images = glob.glob(os.path.join(fmriprepdir, 'fmriprep', '*.html'))

    for report in images:
        logging.info(report)
        shutil.copy(report,
                    os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp',
                                 os.path.basename(report)))

    shutil.make_archive(base_name=output_name,
                        root_dir=os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp'),
                        base_dir=os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp'),
                        format='zip')

    remove_tree(os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp'))
