from nipype.interfaces import afni as afni
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
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, help = 'Use a given configuration file.')
@click.option('-task', help = 'Which task to extract ReHo from. If left blank, defaults to all tasks.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed  traceback for errors.')
def reho_extract(config_file = None, subjects = None, task = None, submit = None, debug = None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    config = ClpipeConfigParser()
    config.config_updater(config_file)

    reho = afni.ReHo()

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config["ReHoExtraction"]['TargetDirectory'])
        if os.path.isdir(os.path.join(config.config["ReHoExtraction"]['TargetDirectory'], o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    batch_manager = BatchManager(config.config['BatchConfig'], config.config["ReHoExtraction"]['LogDirectory'])
    for sub in sublist:
        search_string = os.path.abspath(
            os.path.join(config.config["ReHoExtraction"]['TargetDirectory'], "sub-" + sub, "**",
                         "*" + config.config["ReHoExtraction"]['TargetSuffix']))
        subject_files = glob.glob(search_string, recursive=True)
        if task is not None:
            subject_files = [x for x in subject_files if "task-"+task in x]
            logging.debug(subject_files)
        for file in subject_files:
            reho.inputs.in_file = file
            out_file = os.path.basename(file).replace(config.config["ReHoExtraction"]["TargetSuffix"],config.config["ReHoExtraction"]["OutputSuffix"])
            out_file = os.path.join(config.config["ReHoExtraction"]["OutputDirectory"], out_file)
            reho.inputs.out_file = out_file

            if config.config["ReHoExtraction"]["MaskFileOverride"] is not "":
                reho.inputs.mask_file = config.config["ReHoExtraction"]["MaskFileOverride"]
            else:
                mask_file = file.replace(config.config["ReHoExtraction"]["TargetSuffix"],config.config["ReHoExtraction"]["MaskSuffix"])
                reho.inputs.mask_file = mask_file

            if config.config["ReHoExtraction"]["Neighborhood"] not in ["faces", "edges", "vertices"]:
                raise ValueError("The 'Neighborhood' field must be one of 'faces', 'edges', or 'vertices'")
            reho.inputs.neighborhood = config.config["ReHoExtraction"]["Neighborhood"]

            cmd = reho.cmdline()
            logging.debug(cmd)
            batch_manager.addjob(Job("ReHoExtraction_"+ os.path.basename(file), cmd))
    if submit:
        batch_manager.createsubmissionhead()
        batch_manager.compilejobstrings()
        batch_manager.submit_jobs()
    else:
        batch_manager.createsubmissionhead()
        batch_manager.compilejobstrings()
        click.echo(batch_manager.print_jobs())

