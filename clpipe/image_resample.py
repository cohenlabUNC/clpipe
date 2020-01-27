import os
import glob
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser, GLMConfigParser
import logging
import sys
from .error_handler import exception_handler
from nipype.interfaces import fsl

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = T,
              help='Use a given configuration file.')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')

@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True,
              help='Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def glm_prep(subjects = None, config_file=None, glm_config_file = None,
                     submit=False, batch=True, task=None, debug = None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ClpipeConfigParser()
    config.config_updater(config_file)

    glm_config = GLMConfigParser(glm_config_file)

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config['GLMSetupOptions']['TargetDirectory'])
                   if os.path.isdir(os.path.join(config.config['GLMSetupOptions']['TargetDirectory'], o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    submission_string = '''susan_smoothing -config_file={config} -target_dir={targetDir} -target_suffix={targetSuffix} ''' \
                        '''-output_dir={outputDir} -output_suffix={outputSuffix} {procstream} -log_dir={logOutputDir} {taskString} -single {sub}'''
    task_string = ""
    beta_series_string = ""
    if task is not None:
        task_string = '-task=' + task
    else:
        procstream = ""
    if batch:
        config_string = os.path.abspath(config_file)
        batch_manager = BatchManager(config.config['BatchConfig'], config.config[output_type]['LogDirectory'])
        batch_manager.update_mem_usage(config.config['SUSANOptions']['MemoryUsage'])
        batch_manager.update_time(config.config['SUSANOptions']['TimeUsage'])
        batch_manager.update_nthreads(config.config['SUSANOptions']['NThreads'])
        batch_manager.update_email(config.config["EmailAddress"])
        for sub in sublist:
            sub_string_temp = submission_string.format(
                config=config_string,
                targetDir=config.config[output_type]['TargetDirectory'],
                targetSuffix=config.config[output_type]['TargetSuffix'],
                outputDir=config.config[output_type]['OutputDirectory'],
                outputSuffix=config.config[output_type]['OutputSuffix'],
                procstream=procstream,
                taskString=task_string,
                logOutputDir=config.config[output_type]['LogDirectory'],
                beta_series=beta_series_string,
                sub=sub
            )
            if debug:
                sub_string_temp = sub_string_temp + " -debug"

            batch_manager.addjob(Job("SUSAN" + sub, sub_string_temp))
        if submit:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
        else:
            batch_manager.createsubmissionhead()
            batch_manager.compilejobstrings()
            click.echo(batch_manager.print_jobs())
    else:
        for sub in subjects:

            logging.info('Running Subject ' + sub)
            _glm_prep(glm_config, sub, task)


def _glm_prep(glm_config, subject, task):
    search_string = os.path.abspath(
        os.path.join(glm_config.config["GLMSetupOptions"]['TargetDirectory'], "sub-" + subject, "**",
                     "*" + glm_config.config["GLMSetupOptions"]['TargetSuffix']))

    subject_files = glob.glob(search_string, recursive=True)
    if glm_config.config["GLMSetupOptions"]["SUSANSmoothing"]:
        sus = fsl.SUSAN()
        sus.inputs.brightness_threshold = glm_config.config["GLMSetupOptions"]['SUSANOptions']['BrightnessThreshold']
        sus.inputs.fwhm = glm_config.config["GLMSetupOptions"]['SUSANOptions']['FWHM']
        sus.inputs.output_type = 'NIFTI_GZ'
    logging.info('Finding Image Files')
    for image in subject_files:
        if task is None or 'task-' + task in image:
            logging.info('Processing ' + image)
            try:
                sus.inputs.in_file = image
                sus.inputs.out_file = _build_output_directory_structure(config, image)
                logging.info('Running ' + sus.cmdline)
                result = sus.run()
                logging.debug(result)
            except Exception as err:
                logging.exception(err)

def _build_output_directory_structure(config, filepath):
    output_type = 'SUSANOptions'

    target_directory = filepath[filepath.find('sub-'):]
    target_directory = os.path.dirname(target_directory)
    target_directory = os.path.join(config.config[output_type]['OutputDirectory'], target_directory)
    logging.debug(target_directory)
    os.makedirs(target_directory, exist_ok=True)
    file_name = os.path.basename(filepath)
    sans_ext = os.path.splitext(os.path.splitext(file_name)[0])[0]
    logging.debug(config.config[output_type]['OutputSuffix'])
    file_name = sans_ext + '_' + config.config[output_type]['OutputSuffix']
    logging.debug(file_name)
    return os.path.join(target_directory, file_name)

