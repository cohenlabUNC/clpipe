import click
from .batch_manager import BatchManager,Job
from .config_json_parser import ConfigParser
import os
import parse
import glob
from .error_handler import exception_handler
import sys



@click.command()
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default = None, help = 'The configuration file for the study, use if you have a custom batch configuration.')
@click.option('-conv_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default = None, help = 'The configuration file for the study, use if you have a custom batch configuration.')
@click.option('-dicom_dir', help = 'The folder where subject dicoms are located.')
@click.option('-dicom_dir_format', help = 'Format string for how subjects/sessions are organized within the dicom_dir.')
@click.option('-BIDS_dir', help = 'The dicom info output file name.')
@click.option('-overwrite', is_flag = True, default = False, help = "Overwrite existing BIDS data?")
@click.option('-log_dir', help = 'Where to put the log files. Defaults to Batch_Output in the current working directory.')
@click.option('-submit', is_flag=True, default=False, help = 'Submit jobs to HPC')
def convert2bids(dicom_dir=None, dicom_dir_format=None, bids_dir = None, conv_config_file = None, config_file = None, overwrite = None, log_dir = None, submit = None):
    config = ConfigParser()
    config.config_updater(config_file)
    config.setup_dcm2bids(dicom_dir,
                          conv_config_file,
                          bids_dir,
                          dicom_dir_format,
                          log_dir)

    if not all([config.config['DICOMToBIDSOptions']['DICOMDirectory'],
            config.config['DICOMToBIDSOptions']['BIDSDirectory'],
            config.config['DICOMToBIDSOptions']['ConversionConfig'],
            config.config['DICOMToBIDSOptions']['DICOMFormatString'],
            config.config['DICOMToBIDSOptions']['LogDirectory']]):
        raise ValueError('DICOM directory, BIDS directory, conversion config, log directory and/or format string are not specified.')



    dicom_dir = config.config['DICOMToBIDSOptions']['DICOMDirectory']
    dicom_dir_format = config.config['DICOMToBIDSOptions']['DICOMFormatString']


    formatStr = dicom_dir_format.replace("{subject}", "*")
    session_toggle = False
    if "{session}" in dicom_dir_format:
        session_toggle = True

    formatStr = formatStr.replace("{session}", "*")
    pstring = os.path.join(dicom_dir, dicom_dir_format)
    folders = glob.glob(os.path.join(dicom_dir, formatStr+'/'))
    sub_sess_list = [parse.parse(pstring, x) for x in folders]



    if len(sub_sess_list) == 0:
        sys.excepthook = exception_handler
        raise FileNotFoundError('There are no subjects/sessions found for that format string.')

    if session_toggle:
        conv_string = '''module add dcm2niix; dcm2bids -d {dicom_dir} -o {bids_dir} -p {subject} -s {session} -c {conv_config_file}'''
    else:
        conv_string = '''module add dcm2niix; dcm2bids -d {dicom_dir} -o {bids_dir} -p {subject} -c {conv_config_file}'''

    if overwrite:
        conv_string = conv_string + " --clobber --forceDcm2niix"

    batch_manager = BatchManager(config.config['BatchConfig'], config.config['DICOMToBIDSOptions']['LogDirectory'])
    batch_manager.createsubmissionhead()
    batch_manager.update_mem_usage(config.config['DICOMToBIDSOptions']['MemUsage'])
    batch_manager.update_time(config.config['DICOMToBIDSOptions']['TimeUsage'])
    batch_manager.update_nthreads(config.config['DICOMToBIDSOptions']['CoreUsage'])
    for ind,i in enumerate(sub_sess_list):

        if session_toggle:
             job_id = 'convert_sub-' + i['subject'] + '_ses-' + i['session']
             job1 = Job(job_id, conv_string.format(
                dicom_dir=folders[ind],
                subject = i['subject'],
                session =i['session'],
                conv_config_file = config.config['DICOMToBIDSOptions']['ConversionConfig'],
                bids_dir = config.config['DICOMToBIDSOptions']['BIDSDirectory']
            ))
        else:
            job_id = 'convert_sub-' + i['subject']
            job1 = Job(job_id, conv_string.format(
                dicom_dir=folders[ind],
                subject=i['subject'],
                session=i['session'],
                conv_config_file=config.config['DICOMToBIDSOptions']['ConversionConfig'],
                bids_dir=config.config['DICOMToBIDSOptions']['BIDSDirectory']
            ))
        batch_manager.addjob(job1)

    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
        config.config_json_dump(os.path.dirname(os.path.abspath(config_file)), config_file)
    else:
        batch_manager.print_jobs()


