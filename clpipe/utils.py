import click
import os
import logging
from pathlib import Path

from nipype.utils.filemanip import split_filename


@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def test_func( config_file=None, subjects=None,submit=False, debug=False):
    ctx = click.get_current_context()
    ctx.info_name


def command_log(config):
    ctx = click.get_current_context()
    print(ctx.info_name)
    print(os.getlogin())

def append_suffix(original_path, suffix_to_add):
    """
    Appends on a new suffix to a file path, preserving the exstension.

    Example:

    original_path: sub-01_ses-nov2016_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
    suffix_to_add: extra

    output: sub-01_ses-nov2016_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold_extra.nii.gz
    """
    base, image_name, exstension = split_filename(original_path)
    out_stem = image_name + '_' + suffix_to_add + exstension
    out_file = os.path.join(base, out_stem)

    return out_file


def get_logger(name, debug=False, log_dir=None, f_name="clpipe.log"):
    logger = logging.getLogger("clpipe").getChild(name)

    if debug:
        logger.setLevel(logging.DEBUG)

    if log_dir:
        add_file_handler(log_dir, f_name, logger=logger)

    return logger


def add_file_handler(log_dir: os.PathLike, f_name: str="clpipe.log", 
                     logger: logging.Logger = None):
    if not logger:
        logger = logging.getLogger("clpipe")

    log_dir = Path(log_dir)
    if not log_dir.exists():
        logger.debug(f"Creating log directory: {log_dir}")
        log_dir.mkdir(parents=True)    

    log_file = log_dir / f_name

    # Create log handler
    logger.debug(f"Using log file: {log_file}")
    f_handler = logging.FileHandler(log_file)
    f_handler.setLevel(logging.DEBUG)
    
    # Create log format
    f_format = logging.Formatter('%(asctime)s - %(levelname)s: %(name)s - %(message)s')
    f_handler.setFormatter(f_format)

    # Add handler to the logger
    logger.addHandler(f_handler)
