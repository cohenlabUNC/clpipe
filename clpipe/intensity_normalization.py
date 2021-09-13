import os
import glob
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
import logging
import sys
from .error_handler import exception_handler
from .utils import parse_dir_subjects, build_arg_string
from pathlib import Path

from nipype.interfaces.fsl.maths import MeanImage, BinaryMaths, MedianImage
from nipype.interfaces.fsl.utils import ImageStats
import nipype.pipeline.engine as pe 

RESCALING_10000_GLOBALMEDIAN = "10000_globalmedian"
RESCALING_100_VOXELMEAN = "100_voxelmean"
RESCALING_METHODS = (RESCALING_10000_GLOBALMEDIAN, RESCALING_100_VOXELMEAN)
RESCALING_DEFAULT = RESCALING_10000_GLOBALMEDIAN

#TODO - should be replaced by configuration parser
DEFAULT_TARGET_DIR = Path("data_fmriprep")
DEFAULT_OUTPUT_DIR = Path("data_postproc" / "postproc_normalize")
DEFAULT_NORMALIZATION_SUFFIX = "_normalized"

LOG = logging.getLogger(__name__)

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
#TODO: Flesh out the help messages for new args
@click.option('-rescaling_method', default=RESCALING_DEFAULT)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help='Which directory to process. If a configuration file is provided.')
@click.option('-target_suffix',
              help='Which file suffix to use. If a configuration file is provided with a target suffix, this argument is not necessary. Defaults to "preproc_bold.nii.gz"')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put the normalized data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-output_suffix',
              help='What suffix to append to the normalized files. If a configuration file is provided with a output suffix, this argument is not necessary.')
@click.option('-processing_stream', help = 'Optional processing stream selector.')
@click.option('-log_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put HPC output files. If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True,
              help='Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def intensity_normalization_cli(subjects=None, config_file=None, rescaling_method=None, median_intensity=None, 
                                rescaling_factor=None, target_dir=None, target_suffix=None, output_dir=None,
                                output_suffix=None, log_dir=None, submit=False, batch=False, debug=False):

    intensity_normalization(subjects=subjects, config_file=config_file, rescaling_method=rescaling_method,
        median_intensity=median_intensity, rescaling_factor=rescaling_factor, target_dir=target_dir,
        target_suffix=target_suffix, output_dir=output_dir, output_suffix=output_suffix,
        log_dir=log_dir, submit=submit, batch=batch, debug=debug)
    

def intensity_normalization(subjects:list=None, config_file:str=None, rescaling_method:str=RESCALING_DEFAULT,
                            target_dir:str=DEFAULT_TARGET_DIR, target_suffix=None,
                            output_dir:str=DEFAULT_OUTPUT_DIR, output_suffix=None, log_dir=None, submit=False,
                            batch=True, debug=False):
    """The controller for intensity normalization - handles configuration, input scrubbing, file I/O and method selection.

    Args:
        subjects (list, optional): A list of subjects to process.
        config_file (str, optional): A path to a clpipe configuration file to override the project default.
        rescaling_method (str, optional): The method of normalization to perform. Defaults to RESCALING_DEFAULT.
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

    if debug: LOG.setLevel(logging.DEBUG)
    
    LOG.debug(build_arg_string(subjects=subjects, config_file=config_file, 
        rescaling_method=rescaling_method, target_dir=target_dir,
        target_suffix=target_suffix, output_dir=output_dir, output_suffix=output_suffix,
        log_dir=log_dir, submit=submit, batch=batch, debug=debug))
    
    if rescaling_method not in RESCALING_METHODS: 
        raise ValueError(f"Invalid rescaling method: {rescaling_method}")

    #TODO: build configuration file options
    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.validate_config()

    if subjects is None:
        subjects = parse_dir_subjects(target_dir)
    LOG.info(f"Processing subjects: {subjects}")

    # TODO: Process as nipype workflows
    # TODO: Process these as batch jobs
    # TODO: Path parsing logic
    for subject in subjects:
        LOG.info(f"Rescaling target: {target_dir}")
        LOG.info(f"Rescaling method: {rescaling_method}")

        if rescaling_method == RESCALING_10000_GLOBALMEDIAN:
            calculate_10000_global_median(target_dir, output_dir)
        elif rescaling_method == RESCALING_100_VOXELMEAN:
            calculate_100_voxel_mean(target_dir, output_dir)
        else:
            raise ValueError(f"Invalid rescaling method: {rescaling_method}")

        #TODO: Save image
        LOG.info(f"Rescaling complete and saved to: {output_dir}")

def calculate_10000_global_median(in_path: os.PathLike, out_path:os.PathLike, base_dir: os.PathLike=None):
    """Perform intensity normalization using the 10,000 global median method.

    Args:
        in_path (os.PathLike): A path to an input .nii to normalize.
        out_path (os.PathLike): A path to save the normalized image.
        base_dir (os.PathLike, optional): A path to the base directory for the workflow.
    """
    LOG.info(f"Calculating {RESCALING_10000_GLOBALMEDIAN}")

    median_node = pe.Node(ImageStats(in_file=in_path, op_string="-p 50"), name='global_median')
    mul_10000_node = pe.Node(BinaryMaths(in_file=in_path, operation="mul", operand_value=10000), name="mul_10000")
    div_median_node = pe.Node(BinaryMaths(operation="div", out_file=out_path), name="div_median")

    workflow = pe.Workflow(name='10000_global_median', base_dir=base_dir)
    workflow.connect(mul_10000_node, "out_file", div_median_node, "in_file")
    workflow.connect(median_node, "out_stat", div_median_node, "operand_value")
    workflow.run()

def calculate_100_voxel_mean(in_path: os.PathLike, out_path: os.PathLike, base_dir: os.PathLike=None):
    """Perform intensity normalization using the 100 voxel mean method.

    Args:
        in_path (str): A path to an input .nii to normalize.
        out_path (str): A path to save the normalized image.
    """
    LOG.info(f"Calculating {RESCALING_100_VOXELMEAN}")
    mean_node = pe.Node(MeanImage(in_file=in_path), name='mean')
    mul100_node = pe.Node(BinaryMaths(operation='mul', operand_value=100, in_file=in_path),
        name="mul100")
    div_mean_node = pe.Node(BinaryMaths(operation='div', out_file=out_path), name="div_mean") #operand_file=mean_path

    workflow = pe.Workflow(name='100_voxel_mean', base_dir=base_dir)

    workflow.connect(mul100_node, "out_file", div_mean_node, "in_file")
    workflow.connect(mean_node, "out_file",  div_mean_node, "operand_file")
    workflow.run()