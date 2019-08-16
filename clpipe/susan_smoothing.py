import os
import glob
import click
from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser
import logging
import sys
from .error_handler import exception_handler
from nipype.interfaces import fsl

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
@click.option('-task', help='Which task to smooth. If left blank, defaults to all tasks.')
@click.option('-processing_stream', help = 'Optional processing stream selector.')
@click.option('-log_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put HPC output files. If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True,
              help='Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def susan_smoothing(config_file=None, subjects=None, target_dir=None, target_suffix=None, output_dir=None,
                     output_suffix=None, log_dir=None,
                     submit=False, batch=True, task=None, debug = None, processing_stream = None):
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ConfigParser()
    config.config_updater(config_file)
    config.setup_susan(target_dir, target_suffix, output_dir, output_suffix,
                          log_dir)
    config.validate_config()
    output_type = 'SUSANOptions'

    alt_proc_toggle = False
    if processing_stream is not None:
        processing_stream_config = config.config['ProcessingStreams']
        processing_stream_config = [i for i in processing_stream_config if i['ProcessingStream'] == processing_stream]
        if len(processing_stream_config) == 0:
            raise KeyError('The processing stream you specified was not found.')
        alt_proc_toggle = True

    if alt_proc_toggle:
        config.config['SUSANOptions'].update(processing_stream_config[0]['SUSANOptions'])

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config[output_type]['TargetDirectory'])
                   if os.path.isdir(os.path.join(config.config[output_type]['TargetDirectory'], o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    submission_string = '''susan_smoothing -config_file={config} -target_dir={targetDir} -target_suffix={targetSuffix} ''' \
                        '''-output_dir={outputDir} -output_suffix={outputSuffix} {procstream} -log_dir={logOutputDir} {taskString} -single {sub}'''
    task_string = ""
    beta_series_string = ""
    if task is not None:
        task_string = '-task=' + task
    if processing_stream is not None:
        procstream = "-processing_stream=" + processing_stream
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
            _susan_subject(config, sub, task)


def _susan_subject(config, subject, task):
    output_type = 'SUSANOptions'
    search_string = os.path.abspath(
        os.path.join(config.config[output_type]['TargetDirectory'], "sub-" + subject, "**",
                     "*" + config.config[output_type]['TargetSuffix']))

    subject_files = glob.glob(search_string, recursive=True)
    sus = fsl.SUSAN()
    sus.inputs.brightness_threshold = config.config[output_type]['BrightnessThreshold']
    sus.inputs.fwhm = config.config[output_type]['FWHM']
    sus.inputs.output_type = 'NIFTI_GZ'
    logging.info('Finding Image Files')
    for image in subject_files:
        if task is None or 'task-' + task in image:
            logging.info('Processing ' + image)
            try:
                sus.inputs.in_file = image
                sus.inputs.out_file = _build_output_directory_structure(config, image)
                logging.info('Running ' + sus.cmdline())
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

