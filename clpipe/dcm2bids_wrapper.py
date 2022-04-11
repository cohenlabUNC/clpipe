import click
from .batch_manager import BatchManager,Job
from .config_json_parser import ClpipeConfigParser
import os
import parse
import glob
from .error_handler import exception_handler
import sys

def convert2bids(dicom_dir=None, dicom_dir_format=None, bids_dir=None, conv_config_file=None, config_file=None, overwrite=None, log_dir=None, subject=None, session=None, longitudinal=False, submit=None):
    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.setup_dcm2bids(dicom_dir,
                          conv_config_file,
                          bids_dir,
                          dicom_dir_format,
                          log_dir)

    if not config.config['DICOMToBIDSOptions']['DICOMDirectory']:
        raise ValueError('DICOM directory not specified.')
    if not config.config['DICOMToBIDSOptions']['BIDSDirectory']:
        raise ValueError('BIDS directory not specified.')
    if not config.config['DICOMToBIDSOptions']['ConversionConfig']:
        raise ValueError('Conversion config not specified.')
    if not config.config['DICOMToBIDSOptions']['DICOMFormatString']:
        raise ValueError('Format string not specified.')
    if not config.config['DICOMToBIDSOptions']['LogDirectory']:
        raise ValueError('Log directory not specified.')


    dicom_dir = config.config['DICOMToBIDSOptions']['DICOMDirectory']
    dicom_dir_format = config.config['DICOMToBIDSOptions']['DICOMFormatString']


    formatStr = dicom_dir_format.replace("{subject}", "*")
    session_toggle = False
    if "{session}" in dicom_dir_format:
        session_toggle = True

    formatStr = formatStr.replace("{session}", "*")
    click.echo(formatStr)
    pstring = os.path.join(dicom_dir, dicom_dir_format+'/')
    click.echo(pstring)
    folders = glob.glob(os.path.join(dicom_dir, formatStr+'/'))
    sub_sess_list = [parse.parse(pstring, x) for x in folders]
    sub_inds = [ind for ind, x in enumerate(sub_sess_list)]
    sess_inds = [ind for ind, x in enumerate(sub_sess_list)]
    if subject is not None:
        sub_inds = [ind for ind, x in enumerate(sub_sess_list) if x['subject'] == subject]

    if session is not None:
        sess_inds = [ind for ind, x in enumerate(sub_sess_list) if x['session'] == session]

    sub_sess_inds = list(set(sub_inds) & set(sess_inds))
    folders = [folders[i] for i in sub_sess_inds]
    sub_sess_list = [sub_sess_list[i] for i in sub_sess_inds]
    if len(sub_sess_list) == 0:
        sys.excepthook = exception_handler
        raise FileNotFoundError('There are no subjects/sessions found for that format string.')

    if session_toggle and not longitudinal:
        conv_string = '''dcm2bids -d {dicom_dir} -o {bids_dir} -p {subject} -s {session} -c {conv_config_file}'''
    else:
        conv_string = '''dcm2bids -d {dicom_dir} -o {bids_dir} -p {subject} -c {conv_config_file}'''

    if overwrite:
        conv_string = conv_string + " --clobber --forceDcm2niix"

    batch_manager = BatchManager(config.config['BatchConfig'], config.config['DICOMToBIDSOptions']['LogDirectory'])
    batch_manager.createsubmissionhead()
    batch_manager.update_mem_usage(config.config['DICOMToBIDSOptions']['MemUsage'])
    batch_manager.update_time(config.config['DICOMToBIDSOptions']['TimeUsage'])
    batch_manager.update_nthreads(config.config['DICOMToBIDSOptions']['CoreUsage'])
    for ind,i in enumerate(sub_sess_list):

        if session_toggle and not longitudinal:
             job_id = 'convert_sub-' + i['subject'] + '_ses-' + i['session']
             job1 = Job(job_id, conv_string.format(
                dicom_dir=folders[ind],
                subject = i['subject'],
                session =i['session'],
                conv_config_file = config.config['DICOMToBIDSOptions']['ConversionConfig'],
                bids_dir = config.config['DICOMToBIDSOptions']['BIDSDirectory']
            ))
        elif longitudinal:
            job_id = 'convert_sub-' + i['subject']+ '_ses-' + i['session']
            job1 = Job(job_id, conv_string.format(
                dicom_dir=folders[ind],
                subject=i['subject'] + "sess"+ i['session'],
                conv_config_file=config.config['DICOMToBIDSOptions']['ConversionConfig'],
                bids_dir=config.config['DICOMToBIDSOptions']['BIDSDirectory']
            ))
        else:
            job_id = 'convert_sub-' + i['subject']
            job1 = Job(job_id, conv_string.format(
                dicom_dir=folders[ind],
                subject=i['subject'],
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


