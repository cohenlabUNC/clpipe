from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
import os
import parse
import glob
import sys

from .utils import get_logger, add_file_handler

BASE_CMD = ("dcm2bids -d {dicom_dir} -o {bids_dir} "
            "-p {subject} -c {conv_config_file}")

def convert2bids(dicom_dir=None, dicom_dir_format=None, bids_dir=None, 
                 conv_config_file=None, config_file=None, overwrite=None, 
                 log_dir=None, subject=None, session=None, longitudinal=False, 
                 submit=None, debug=False):
    
    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.setup_dcm2bids(dicom_dir,
                          conv_config_file,
                          bids_dir,
                          dicom_dir_format,
                          log_dir)

    project_dir = config.config["ProjectDirectory"]
    dicom_dir = config.config['DICOMToBIDSOptions']['DICOMDirectory']
    dicom_dir_format = config.config['DICOMToBIDSOptions']['DICOMFormatString']
    bids_dir = config.config['DICOMToBIDSOptions']['BIDSDirectory']
    conv_config = config.config['DICOMToBIDSOptions']['ConversionConfig']
    log_dir = config.config['DICOMToBIDSOptions']['LogDirectory']
    batch_config = config.config['BatchConfig']
    mem_usage = config.config['DICOMToBIDSOptions']['MemUsage']
    time_usage = config.config['DICOMToBIDSOptions']['TimeUsage']
    n_threads = config.config['DICOMToBIDSOptions']['CoreUsage']

    add_file_handler(os.path.join(project_dir, "logs"))
    logger = get_logger("bids-conversion", debug=debug)

    if not dicom_dir:
        logger.error('DICOM directory not specified.')
        sys.exit(1)
    if not bids_dir:
        logger.error('BIDS directory not specified.')
        sys.exit(1)
    if not conv_config:
        logger.error('Conversion config not specified.')
        sys.exit(1)
    if not dicom_dir_format:
        logger.error('Format string not specified.')
        sys.exit(1)
    if not log_dir:
        logger.error('Log directory not specified.')
        sys.exit(1)

    logger.info(f"Starting bids conversion targeting: {dicom_dir}")

    format_str = dicom_dir_format.replace("{subject}", "*")
    session_toggle = False
    if "{session}" in dicom_dir_format:
        session_toggle = True

    format_str = format_str.replace("{session}", "*")
    logger.debug(f"Format string: {format_str}")

    pstring = os.path.join(dicom_dir, dicom_dir_format+'/')
    logger.debug(f"pstring: {pstring}")
    
    folders = glob.glob(os.path.join(dicom_dir, format_str+'/'))
    sub_sess_list = [parse.parse(pstring, x) for x in folders]
    sub_inds = [ind for ind, x in enumerate(sub_sess_list)]
    sess_inds = [ind for ind, x in enumerate(sub_sess_list)]
    
    if subject is not None:
        sub_inds = [ind for ind, x in enumerate(sub_sess_list) \
            if x['subject'] == subject]
    if session is not None:
        sess_inds = [ind for ind, x in enumerate(sub_sess_list) \
            if x['session'] == session]

    sub_sess_inds = list(set(sub_inds) & set(sess_inds))
    folders = [folders[i] for i in sub_sess_inds]
    sub_sess_list = [sub_sess_list[i] for i in sub_sess_inds]
    if len(sub_sess_list) == 0:
        logger.error((f'There are no subjects/sessions found for format '
                       'string: {format_str}'))
        sys.exit(1)

    conv_string = BASE_CMD
    if session_toggle and not longitudinal:
        conv_string += " -s {session}"

    if overwrite:
        conv_string = conv_string + " --clobber --forceDcm2niix"

    batch_manager = BatchManager(batch_config, log_dir, debug=debug)
    batch_manager.createsubmissionhead()
    batch_manager.update_mem_usage(mem_usage)
    batch_manager.update_time(time_usage)
    batch_manager.update_nthreads(n_threads)

    for ind,i in enumerate(sub_sess_list):
        if session_toggle and not longitudinal:
            job_id = 'convert_sub-' + i['subject'] + '_ses-' + i['session']
            job1 = Job(
                job_id, conv_string.format(
                    dicom_dir = folders[ind],
                    subject = i['subject'],
                    session = i['session'],
                    conv_config_file = conv_config,
                    bids_dir = bids_dir
                )
            )
        elif longitudinal:
            job_id = 'convert_sub-' + i['subject']+ '_ses-' + i['session']
            job1 = Job(
                job_id, conv_string.format(
                    dicom_dir = folders[ind],
                    subject = i['subject'] + "sess"+ i['session'],
                    conv_config_file = conv_config,
                    bids_dir = bids_dir
                )
            )
        else:
            job_id = 'convert_sub-' + i['subject']
            job1 = Job(
                job_id, conv_string.format(
                    dicom_dir = folders[ind],
                    subject = i['subject'],
                    conv_config_file = conv_config,
                    bids_dir = bids_dir
                )
            )
        batch_manager.addjob(job1)

    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
        config.config_json_dump(os.path.dirname(os.path.abspath(config_file)),
                                config_file)
    else:
        batch_manager.print_jobs()
        logger.info("Rerun with the '-submit' flag to launch these jobs.")
