import click
import os
import sys
import logging
from pathlib import Path

from nipype.utils.filemanip import split_filename


@click.command()
@click.argument("subjects", nargs=-1, required=False, default=None)
@click.option(
    "-config_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    help="Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.",
)
@click.option(
    "-submit", is_flag=True, default=False, help="Flag to submit commands to the HPC"
)
@click.option(
    "-debug", is_flag=True, help="Flag to enable detailed error messages and traceback"
)
def test_func(config_file=None, subjects=None, submit=False, debug=False):
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
    out_stem = image_name + "_" + suffix_to_add + exstension
    out_file = os.path.join(base, out_stem)

    return out_file


def resolve_fmriprep_dir_new(fmriprep_dir):
    fmriprep_root = fmriprep_dir
    if os.path.exists(fmriprep_root) and not os.path.exists(
        os.path.join(fmriprep_root, "fmriprep")
    ):
        return os.path.abspath(fmriprep_root)
    elif os.path.exists(fmriprep_root) and os.path.exists(
        os.path.join(fmriprep_root, "fmriprep")
    ):
        fmriprep_root = os.path.join(fmriprep_root, "fmriprep")
        return os.path.abspath(fmriprep_root)
    else:
        fmriprep_root = os.path.join(fmriprep_dir, os.pardir)
        return os.path.abspath(fmriprep_root)


def resolve_fmriprep_dir(fmriprep_dir):
    """Support fMRIPrep the folder structure in version < 21 or version > 21.

    Check to see if a subdirectory named fmriprep is in the target directory
    version < 21 of fMRIPrep has a folder named 'fmriprep' nested within its output.
    If this exists, return this path as fmriprep's root directory.
    If not, use the given fmriprep path directly.

    Even if the user is using < 21 and overspecifies the path as data_fmriprep/fmriprep,
    this will still give the desired root fmriprep directory.
    """
    old_fmriprep_layer = os.path.join(fmriprep_dir, "fmriprep")
    fmriprep_root = fmriprep_dir
    if os.path.exists(old_fmriprep_layer):
        fmriprep_root = old_fmriprep_layer

    return fmriprep_root

def exception_handler(exception_type, exception, traceback):
    print("%s: %s" % (exception_type.__name__, exception))


def get_logger(name, debug=False, log_dir=None, f_name="clpipe.log"):
    logger = logging.getLogger("clpipe").getChild(name)

    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    # if debug:
    #     logger.setLevel(logging.DEBUG)

    if log_dir:
        add_file_handler(log_dir, f_name, logger=logger)

    user_name = ""

    try:
        user_name = os.getlogin()
    except OSError:
        # Fallback for if first option fails, usually due to running clpipe on a
        #   compute node
        user_name = Path.home().stem
    except:
        # Ultimate fallback if neither works
        user_name = "unknown"

    log_args = {"username": user_name}

    logger = logging.LoggerAdapter(logger, log_args)
    return logger


def add_file_handler(
    log_dir: os.PathLike, f_name: str = "clpipe.log", logger: logging.Logger = None
):
    if not logger:
        logger = logging.getLogger("clpipe")

    log_dir = Path(log_dir)
    if not log_dir.exists():
        logger.debug(f"Creating log directory: {log_dir}")
        log_dir.mkdir(parents=True)

    log_file = log_dir / f_name

    # Create log handler
    logger.debug(f"Using log file: {log_file}")

    if (not log_file.is_file()) or (
        log_file.is_file() and os.access(log_file, os.W_OK)
    ):
        f_handler = logging.FileHandler(log_file)
        f_handler.setLevel(logging.DEBUG)

        # Create log format
        f_format = logging.Formatter(
            "%(asctime)s - %(username)s - %(levelname)s: %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        f_handler.setFormatter(f_format)

        # Add handler to the logger
        logger.addHandler(f_handler)
        return
    else:
        logger.error(
            f"User does not have write permissions for the Log File at: {log_file}"
        )
        exit(1)
