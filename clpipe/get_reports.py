from .config_json_parser import ClpipeConfigParser
import os
import glob
import shutil
from distutils.dir_util import copy_tree, remove_tree
from tqdm import tqdm
from .utils import add_file_handler, get_logger, resolve_fmriprep_dir

STEP_NAME = "reports_fmriprep"

def get_reports(config_file, output_name, debug, clear_temp=True):
    """This command creates a zip archive of fmriprep QC reports for download."""
    if config_file is None:
        raise ValueError('Please specify a configuration file.')

    config = ClpipeConfigParser()
    config.config_updater(config_file)

    project_dir = config.config["ProjectDirectory"]

    add_file_handler(os.path.join(project_dir, "logs"))
    logger = get_logger(STEP_NAME, debug=debug)

    fmriprepdir = config.config['FMRIPrepOptions']['OutputDirectory']

    logger.info(f"Generating an fMRIPrep report targeting: {fmriprepdir}")
    logger.debug(f"Using config file: {config_file}")

    fmriprepdir = resolve_fmriprep_dir(fmriprepdir)

    image_dirs = [f.path for f in os.scandir(fmriprepdir) if f.is_dir()]

    logger.info(f"Copying figures:")
    for sub in tqdm([x for x in image_dirs if 'sub-' in x], ascii=' #'):
        copy_tree(os.path.join(sub, 'figures'),
                  os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp', 'fmriprep_reports',
                               os.path.basename(sub), 'figures'))
        ses_dirs = [f.path for f in os.scandir(sub) if f.is_dir()]
        for ses in [x for x in ses_dirs if 'ses-' in x]:
            if os.path.isdir(os.path.join(ses, 'figures')):
                   copy_tree(os.path.join(ses, 'figures'),
                        os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp', 'fmriprep_reports',
                                   os.path.basename(sub),os.path.basename(ses), 'figures'))
    images = glob.glob(os.path.join(fmriprepdir, '*.html'))

    logger.info(f"Copying reports...")
    for report in images:
        shutil.copyfile(report,
                    os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp', 'fmriprep_reports',
                                 os.path.basename(report)))

    logger.info(f"Creating ZIP archive...")
    shutil.make_archive(base_name=output_name,
                        root_dir=os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp'),
                        base_dir='fmriprep_reports',
                        format='zip')

    if clear_temp:
        logger.info(f"Removing temporary directory...")
        remove_tree(os.path.join(config.config['FMRIPrepOptions']['WorkingDirectory'], 'reports_temp'))

    logger.info(f"Job finished. ZIP file created at: {output_name}")
