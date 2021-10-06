import os
import glob
import pathlib
import click

from clpipe.postprocutils.utils import apply_filter
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
import logging
import sys
from .error_handler import exception_handler
from .utils import parse_dir_subjects, build_arg_string
from pathlib import Path
from collections.abc import Callable

from nipype.interfaces.fsl.maths import MeanImage, BinaryMaths, MedianImage
from nipype.interfaces.fsl.utils import ImageStats
import nipype.pipeline.engine as pe
import nibabel as nib

from postprocutils.utils import calc_filter, apply_filter

RESCALING_10000_GLOBALMEDIAN = "10000_globalmedian"
RESCALING_100_VOXELMEAN = "100_voxelmean"
NORMALIZATION_METHODS = (RESCALING_10000_GLOBALMEDIAN, RESCALING_100_VOXELMEAN)

LOG = logging.getLogger(__name__)

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
#TODO: Flesh out the help messages for new args
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help='Which directory to process. If a configuration file is provided.')
@click.option('-target_suffix',
              help='Which file suffix to use. If a configuration file is provided with a target suffix, this argument is not necessary. Defaults to "preproc_bold.nii.gz"')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put the normalized data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-output_suffix')
@click.option('-log_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put HPC output files. If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True,
              help='Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
@click.option('-normalization_method', default=None)
def hngprep_cli(subjects=None, config_file=None, target_dir=None, target_suffix=None, output_dir=None,
                output_suffix=None, log_dir=None, submit=False, batch=False, debug=False,
                normalization_method=None,):

    hngprep(subjects=subjects, config_file=config_file, target_dir=target_dir, target_suffix=target_suffix, output_dir=output_dir,
            output_suffix=output_suffix, log_dir=log_dir, submit=submit, batch=batch, debug=debug,
            normalization_method=normalization_method)
    

def hngprep(subjects:list=None, config_file:str=None, normalization_method:str=None,
            target_dir:str=None, target_suffix=None,
            output_dir:str=None, output_suffix=None, log_dir=None, submit=False,
            batch=True, debug=False):
    """The controller for intensity normalization - handles configuration, input scrubbing, file I/O and method selection.

    Args:
        subjects (list, optional): A list of subjects to process.
        config_file (str, optional): A path to a clpipe configuration file to override the project default.
        normalization_method (str, optional): The method of normalization to perform. Defaults to RESCALING_DEFAULT.
        target_dir (str, optional): A path to the directory of images to normalize. Defaults to DEFAULT_TARGET_DIR.
        target_suffix (str, optional): [description]. Defaults to None.
        output_dir (str): A path to the output directory of normalized images.
        output_suffix (str, optional): [description]. Defaults to None.
        log_dir (str, optional): A path to a logging directory. Overrides default in project configuration. Defauts to None.
        submit (bool, optional): Indicate whether or not to submit as job. Defaults to False.
        batch (bool, optional): Indicate whether to process individual subject or batch of subjects. Defaults to True.
        debug (bool, optional): Raise verbosity of logging. Defaults to False.

    Raises:
        ValueError: Thrown if provided a non-valid normalization method
    """

    #TODO: logging and config setup is probably generalizable
    if debug: LOG.setLevel(logging.DEBUG)
    
    LOG.debug(build_arg_string(subjects=subjects, config_file=config_file, 
        rescaling_method=method, target_dir=target_dir,
        target_suffix=target_suffix, output_dir=output_dir, output_suffix=output_suffix,
        log_dir=log_dir, submit=submit, batch=batch, debug=debug))

    # Pull in current configuration
    config = ClpipeConfigParser()
    # If provided, override project config with parameter config
    config.config_updater(config_file)
    # For those provided, replace intensity normalization config values with parameter values
    # TODO: Implement input params
    # config.setup_hngprep(target_dir, target_suffix, output_dir, output_suffix, method, log_dir)
    hngprep_config = config.config["HNGPrepOptions"]

    target_dir = Path(hngprep_config["TargetDirectory"])
    normalization_method = config["IntensityNormalizationMethod"]
 
    # Validate the provided rescaling method
    if normalization_method not in NORMALIZATION_METHODS: 
        raise ValueError(f"Invalid rescaling method: {method}")

    if subjects is None:
        subjects = parse_dir_subjects(str(target_dir))
    LOG.info(f"Processing subjects: {subjects}")

    # TODO: Process these as batch jobs
    for subject in subjects:
        hngprep_subject(hngprep_config, f'sub-{subject}')


def _get_normalization_method(method_str: str) -> Callable:
    if method_str == RESCALING_10000_GLOBALMEDIAN:
        return calculate_10000_global_median
    elif method_str == RESCALING_100_VOXELMEAN:
        return calculate_100_voxel_mean
    else:
        raise ValueError(f"Invalid rescaling method: {method}")

def append_suffix(base_path: Path, suffix: str) -> Path:
    filename = base_path.name
    for extension in base_path.suffixes:
        filename = filename.replace(extension, '')

    return f"{filename}_{suffix}"

def hngprep_subject(config: ClpipeConfigParser, subject: str):

    config = config.config['HNGPrepOptions']
    target_dir = Path(config['TargetDirectory'])
    output_dir = Path(config['OutputDirectory'])
    target_suffix = config['TargetSuffix']
    output_suffix = config['OutputSuffix']
    normalization_method_str = config['Method']
    log_dir = Path(config['LogDirectory'])

    normalization_method: Callable = _get_normalization_method(normalization_method_str)
    temporal_filtering_method: Callable = None

    sub_output_dir = output_dir / subject

    if not sub_output_dir.exists():
        LOG.info(f"Creating directory: f{str(sub_output_dir)}")
        sub_output_dir.mkdir(parents=True, exist_ok=True)

    for image_path in target_dir.glob(f'{subject}/**/*{target_suffix}*'):
        LOG.info(f"HNGPrep target: {target_suffix}")
        LOG.info(f"Normalization method: {normalization_method.__name__}")
        
        output_path = sub_output_dir / append_suffix(image_path, output_suffix)

        normalization_workflow = normalization_method(image_path, output_path, base_dir=log_dir, crashdump_dir=log_dir)

        LOG.info(f"Rescaling complete and saved to: {output_path}")

