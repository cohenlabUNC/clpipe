import os
import glob
import click
import pandas
from nipy import load_image
from nipy.core.image.image import Image
from nipy import save_image
from .batch_manager import BatchManager, Job
from .config_json_parser import ConfigParser
import json
from pkg_resources import resource_stream, resource_filename
import clpipe.postprocutils
import numpy
import logging
import gc
import psutil
import sys
from .error_handler import exception_handler
import nipy.modalities.fmri.hrf


@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help='Which fmriprep directory to process. If a configuration file is provided with a BIDS directory, this argument is not necessary. Note, must point to the ``fmriprep`` directory, not its parent directory.')
@click.option('-target_suffix',
              help='Which file suffix to use. If a configuration file is provided with a target suffix, this argument is not necessary. Defaults to "preproc_bold.nii.gz"')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put the postprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-output_suffix',
              help='What suffix to append to the postprocessed files. If a configuration file is provided with a output suffix, this argument is not necessary.')
@click.option('-task', help='Which task to postprocess. If left blank, defaults to all tasks.')
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
    """This command runs an fMRIprep'ed dataset through additional processing, as defined in the configuration file. To run specific subjects, specify their IDs. If no IDs are specified, all subjects are ran."""
    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    if config_file is None and tr is None:
        raise ValueError('No config file and no specified TR. Please include one.')

    config = ConfigParser()
    config.config_updater(config_file)
    config.setup_susan(target_dir, target_suffix, output_dir, output_suffix, beta_series,
                          log_dir)
    config.validate_config()
    output_type = 'BetaSeriesOptions'

    alt_proc_toggle = False
    if processing_stream is not None:
        processing_stream_config = config.config['ProcessingStreams']
        processing_stream_config = [i for i in processing_stream_config if i['ProcessingStream'] == processing_stream]
        if len(processing_stream_config) == 0:
            raise KeyError('The processing stream you specified was not found.')
        alt_proc_toggle = True

    if alt_proc_toggle:
        config.config['PostProcessingOptions'].update(processing_stream_config[0]['SUSANOptions'])

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
    tr_string = ""
    beta_series_string = ""
    if task is not None:
        task_string = '-task=' + task
    if processing_stream is not None:
        procstream = "-processing_stream=" + processing_stream
    else:
        procstream = ""
    if batch:
        config_string = config.config_json_dump(config.config[output_type]['OutputDirectory'],
                                                os.path.basename(config_file))
        batch_manager = BatchManager(config.config['BatchConfig'], config.config[output_type]['LogDirectory'])
        batch_manager.update_mem_usage(config.config['PostProcessingOptions']['PostProcessingMemoryUsage'])
        batch_manager.update_time(config.config['PostProcessingOptions']['PostProcessingTimeUsage'])
        batch_manager.update_nthreads(config.config['PostProcessingOptions']['NThreads'])
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
                trString=tr_string,
                logOutputDir=config.config[output_type]['LogDirectory'],
                beta_series=beta_series_string,
                sub=sub
            )
            if debug:
                sub_string_temp = sub_string_temp + " -debug"

            batch_manager.addjob(Job("PostProcessing" + sub, sub_string_temp))
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
            logging.debug(beta_series)
            logging.info('Running Subject ' + sub)
            _fmri_postprocess_subject(config, sub, task, tr, beta_series)


def _fmri_postprocess_subject(config, subject, task, tr=None, beta_series=False):
    if beta_series:
        output_type = 'BetaSeriesOptions'
    else:
        output_type = 'PostProcessingOptions'
    search_string = os.path.abspath(
        os.path.join(config.config[output_type]['TargetDirectory'], "sub-" + subject, "**",
                     "*" + config.config[output_type]['TargetSuffix']))

    subject_files = glob.glob(search_string, recursive=True)
    logging.info('Finding Image Files')
    for image in subject_files:
        if task is None or 'task-' + task in image:
            logging.info('Processing ' + image)
            try:
                _fmri_postprocess_image(config, image, task, tr, beta_series)
            except Exception as err:
                logging.exception(err)