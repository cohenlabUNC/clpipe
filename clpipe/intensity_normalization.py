import os
import glob
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
import logging
import sys
from .error_handler import exception_handler

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help='Which directory to process. If a configuration file is provided.')
@click.option('-target_suffix',
              help='Which file suffix to use. If a configuration file is provided with a target suffix, this argument is not necessary. Defaults to "preproc_bold.nii.gz"')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put the postprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-output_suffix',
              help='What suffix to append to the smoothed files. If a configuration file is provided with a output suffix, this argument is not necessary.')
@click.option('-processing_stream', help = 'Optional processing stream selector.')
@click.option('-log_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put HPC output files. If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True,
              help='Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def intensity_normalization_cli(config_file=None, fmri_derivatives=None, output_dir=None,
                     output_suffix=None, log_dir=None,
                     submit=False, batch=True, task=None, debug = None):
    intensity_normalization(config_file=config_file, fmri_derivatives=fmri_derivatives, output_dir=output_dir,
        output_suffix=output_suffix, log_dir=log_dir, submit=submit, batch=batch, debug=debug)
    

def intensity_normalization(config_file=None, fmri_derivatives=None, output_dir=None,
                        output_suffix=None, log_dir=None,
                        submit=False, batch=True, debug = None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    logging.debug(build_arg_string(config_file=config_file, fmri_derivatives=fmri_derivatives, output_dir=output_dir,
        output_suffix=output_suffix, log_dir=log_dir, submit=submit, batch=batch, debug=debug))

    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.validate_config()

def build_arg_string(**kwargs):
    out = " Submitted Args:\n"
    for arg in kwargs:
        out += f"\t{arg}: {str(kwargs[arg])}\n"

    return(out)
        
    

