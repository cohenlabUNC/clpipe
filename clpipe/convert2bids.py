from pathlib import Path
from .batch_manager import BatchManager, Job
from .config.options import ProjectOptions
import os
import parse
import glob
import click
import logging

from .utils import get_logger
from .status import needs_processing, write_record

# These imports are for the heudiconv converter
from pkg_resources import resource_filename

INFO_COMMAND_NAME = "dicom-info"
STEP_NAME = "bids-conversion"
BASE_CMD = ("dcm2bids -d {subject_dicom_dir} -o {bids_dir} "
            "-p {subject} -c {conv_config_file}")
HEUDICONV_BASE_CMD = '''heudiconv --files {subject_dicom_dir} -s {subject} '''\
        '''-f {heuristic} -o {output_directory} -b'''
DEFAULT_CONV_CONFIG_PATH = "data/default_conv_config.json"



def convert2bids(dicom_dir=None, dicom_dir_format=None, bids_dir=None, 
                 conv_config_file=None, config_file=None, overwrite=False, 
                 clear_cache=False, clear_outputs=False, log_dir=None, subject=None,
                 subjects=None, session=None, 
                 longitudinal=False, status_cache=None, submit=False, debug=False, 
                 dcm2bids=True, batch=False):
    
    config: ProjectOptions = ProjectOptions.load(config_file)
    config.convert2bids.load_cli_args(dicom_dir, dicom_dir_format, conv_config_file, bids_dir, log_dir)

    setup_dirs(config)

    logger = get_logger(STEP_NAME, debug=debug, log_dir=Path(config.project_directory) / "logs")

    batch_manager = BatchManager(config.batch_config_path, log_dir, debug=debug)
    batch_manager.create_submission_head()
    batch_manager.update_mem_usage(config.convert2bids.mem_usage)
    batch_manager.update_time(config.convert2bids.time_usage)
    batch_manager.update_nthreads(config.convert2bids.core_usage)

    logger.info(f"Starting BIDS conversion targeting: {config.convert2bids.dicom_directory}")
    logger.debug(f"Using config file: {config_file}")

    # Pack a single subject into list
    if subject and not subjects:
        subjects = [subject]
        logger.warn("WARNING: The -subject option is deprecated. "
            "You can now pass an arbitrary number of subjects "
            "as command line arguments.")
    
    if dcm2bids:
        logger.info("Using converter: dcm2bids")

        # move sub / session detection code to seperate function to try with heudiconv
        dcm2bids_wrapper(
            dicom_dir=config.convert2bids.dicom_directory,
            dicom_dir_format=config.convert2bids.dicom_format_string, 
            bids_dir=config.convert2bids.bids_directory,
            conv_config=config.convert2bids.conversion_config,
            overwrite=overwrite, subjects=subjects, session=session, 
            longitudinal=longitudinal, 
            submit=submit, status_cache=status_cache,
            logger=logger, batch_manager=batch_manager)

    elif not dcm2bids:
        logger.info("Using converter: heudiconv")

        heudiconv_wrapper(
            subjects=subjects, session=session, dicom_dir=config.convert2bids.dicom_directory, submit=submit,
            output_directory=config.convert2bids.bids_directory, heuristic_file=config.convert2bids.conversion_config,
            overwrite=overwrite, batch_manager=batch_manager, logger=logger,
            dicom_dir_format=config.convert2bids.dicom_format_string, clear_cache=clear_cache, 
            clear_outputs=clear_outputs, longitudinal=longitudinal)

    else:
        logger.error("Must specificy one of either 'conv_config' or 'heuristic'")


def dcm2bids_wrapper(
    dicom_dir: os.PathLike, 
    bids_dir: os.PathLike, 
    conv_config: os.PathLike, 
    dicom_dir_format: str, 
    batch_manager: BatchManager,
    logger: logging.Logger,
    subjects: str=None,
    session: str=None,
    longitudinal: bool=False,
    overwrite: bool=None, 
    status_cache: os.PathLike=None,
    submit: bool=None
    ):

    sub_sess_list, folders = _get_sub_session_list(dicom_dir, dicom_dir_format, logger,
        subjects=subjects, session=session)

    if len(sub_sess_list) == 0:
        logger.warn((f'There were no subjects/sessions found for format '
                    f'string: {dicom_dir_format}'))
        return

    conv_string = BASE_CMD
    session_toggle = "{session}" in dicom_dir_format
    
    if session_toggle and not longitudinal:
        conv_string += " -s {session}"
    if overwrite:
        conv_string = conv_string + " --clobber --forceDcm2niix"

    subjects_to_process = [result['subject'] for result in sub_sess_list]
    logger.debug(f"Subjects to process: {subjects_to_process}")

    # Default to processing all subjects
    subjects_need_processing = subjects_to_process
    # Reduce subjects to process based on cache if provided
    if status_cache:
        # TODO: Handle subject/session
        subjects_need_processing = needs_processing(
            subjects_to_process, status_cache
        )
    logger.debug(f"Subjects need processing: {subjects_need_processing}")

    # Create jobs using the sub/sess list
    for ind, i in enumerate(sub_sess_list):
        subject = i['subject']

        # Create a dict of args with which to format conv_string
        conv_args = {
            "subject_dicom_dir": folders[ind], 
            "conv_config_file": conv_config,
            "bids_dir": bids_dir,
            "subject": subject
        }
        job_id = 'convert_sub-' + subject

        if session_toggle:
            job_id += '_ses-' + i['session']
            conv_args["session"] = i['session']
        if longitudinal:
            conv_args["subject"] += "sess"+ i['session']

        # Unpack the conv_args
        submission_string = conv_string.format(**conv_args)

        job = Job(job_id, submission_string)

        if subject in subjects_need_processing:
            batch_manager.addjob(job)

    batch_manager.compile_job_strings()
    if submit:
        if len(subjects_need_processing) > 0:
            logger.info(
                f"Converting subject(s): {', '.join(subjects_need_processing)}"
            )
            batch_manager.submit_jobs()
            
            if status_cache:
                for subject in subjects_need_processing:
                    write_record(subject, cache_path = status_cache)
        else:
            logger.info("No subjects need processing.")
    else:
        batch_manager.print_jobs()


def heudiconv_wrapper(
    dicom_dir: os.PathLike,
    output_directory: os.PathLike,
    heuristic_file: os.PathLike,
    dicom_dir_format: str,
    batch_manager: BatchManager,
    logger: logging.Logger,
    subjects: list=None,
    session: str=None,
    longitudinal: bool=False,
    overwrite: bool=False,
    clear_cache: bool=False,
    clear_outputs: bool=False,
    submit: bool=False
    ):
    """
    This command uses heudiconv to convert dicoms into BIDS formatted NiFTI files. 
    Users can specify any number of subjects, or leave subjects blank to convert all 
    subjects. 
    """

    session_toggle = "{session}" in dicom_dir_format

    sub_sess_list, folders = _get_sub_session_list(dicom_dir, dicom_dir_format, logger,
        session=session, subjects=subjects)

    if len(sub_sess_list) == 0:
        logger.warn((f'There were no subjects/sessions found for format '
                    f'string: {dicom_dir_format}'))
        return
        
    subjects_to_process = [result['subject'] for result in sub_sess_list]
    logger.debug(f"Subjects to process: {subjects_to_process}")


    dicom_dir_template = str(Path(dicom_dir) / dicom_dir_format)
    logger.debug(f"dicom_dir_template: {dicom_dir_template}")

    if session:
        if '{session}' not  in dicom_dir_format:
            raise ValueError("Session value given but no '{session}' placeholder found in dicom_dir_format")
        logger.debug("Session toggle: ON")
    else:
        logger.debug("Session toggle: OFF")

    heudiconv_string = HEUDICONV_BASE_CMD
    if session_toggle and not longitudinal:
        heudiconv_string += " -ss {session}"
    if overwrite:
        heudiconv_string += " --overwrite"

   # Create jobs using the sub/sess list
    for ind, i in enumerate(sub_sess_list):
        subject = i['subject']

        job_id = 'convert_sub-' + subject
        
        job_args = {
            "subject_dicom_dir": folders[ind],
            "subject": subject,
            "heuristic": heuristic_file,
            "output_directory" : output_directory
        }
        if session_toggle:
            job_id += '_ses-' + i['session']
            job_args["session"] = i['session']
        if longitudinal:
            job_args["subject"] += "sess"+ i['session']

        job_str = heudiconv_string.format(**job_args)

        if clear_cache:
            clear_cache_cmd = f"rm -r {output_directory}/.heudiconv/{i['subject']}"
            job_str = clear_cache_cmd + "; " + job_str
        if clear_outputs:
            clear_bids_cmd = f"rm -r {output_directory}/sub-{i['subject']}"
            job_str = clear_bids_cmd + "; " + job_str

        job = Job(job_id, job_str)
        batch_manager.add_job(job)
    
    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()


def _get_sub_session_list(dicom_dir, dicom_dir_format, logger, subjects=None, session=None):
    logger.debug(f"Format string: {dicom_dir_format}")

    format_str = dicom_dir_format.replace("{subject}", "*")
    format_str = format_str.replace("{session}", "*")
    
    pstring = os.path.join(dicom_dir, dicom_dir_format+'/')
    logger.debug(f"pstring: {pstring}")
    
    # Get all folders in the dicom_dir
    folders = glob.glob(os.path.join(dicom_dir, format_str+'/'))
    # Parse the subject id and/or session id from the folder names
    sub_sess_list = [parse.parse(pstring, x) for x in folders]

    # Create a list of indexes for both subjects and sessions
    sub_inds = [ind for ind, x in enumerate(sub_sess_list)]
    sess_inds = [ind for ind, x in enumerate(sub_sess_list)]
    
    # Narrow down the index lists to the requested subjects/sessions
    if subjects:
        sub_inds = [ind for ind, x in enumerate(sub_sess_list) \
            if x['subject'] in subjects]
    if session is not None:
        sess_inds = [ind for ind, x in enumerate(sub_sess_list) \
            if x['session'] == session]

    # Find the intersection of subject and session indexes
    sub_sess_inds = list(set(sub_inds) & set(sess_inds))

    # Pick the relevant folders using the remaining indexes
    folders = [folders[i] for i in sub_sess_inds]
    # Pick the relevant subject sessions using the remaining indexes
    sub_sess_list = [sub_sess_list[i] for i in sub_sess_inds]

    return sub_sess_list, folders


def setup_dirs(config):
    from pkg_resources import resource_stream
    import json

    # Create the step's core directories
    os.makedirs(config.convert2bids.bids_directory, exist_ok=True)
    os.makedirs(config.convert2bids.log_directory, exist_ok=True)

    # Create the default conversion config file
    if not os.path.exists(config.convert2bids.conversion_config):
        with resource_stream(__name__, DEFAULT_CONV_CONFIG_PATH) as def_conv_config:
            conv_config = json.load(def_conv_config)
        
            with open(config.convert2bids.conversion_config, 'w') as fp:
                json.dump(conv_config, fp, indent='\t')
        
    # Create a default .bidsignore file
    bids_ignore_path = os.path.join(config.convert2bids.bids_directory, ".bidsignore")
    if not os.path.exists(bids_ignore_path):
        with open(bids_ignore_path, 'w') as bids_ignore_file:
            # Ignore dcm2bid's auto-generated directory
            bids_ignore_file.write("tmp_dcm2bids\n")
            # Ignore heudiconv's auto-generated scan file
            bids_ignore_file.write("scans.json\n")


@click.command(INFO_COMMAND_NAME)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default = None, help = 'The configuration file for the study, use if you have a custom batch configuration.')
@click.option('-subject', required=True, default=None, help = 'A subject that has all scans of interest present.')
@click.option('-session', default=None, help = 'A session indicator, if sessions are present')
@click.option('-dicom_directory', required = True, help = 'The specially formatted dicom directory string. Please see help pages at https://clpipe.readthedocs.io/en/latest/index.html for more details')
@click.option('-output_file', default = "dicom_info.tsv", help = 'The dicom info output file name.')
@click.option('-submit', is_flag = True, default=False, help = 'Submission job to HPC.')
def dicom_to_nifti_to_bids_converter_setup(subject = None, session = None, dicom_directory=None, output_file=None, config_file = None,  submit=False):
    """This command can be used to compute and extract a dicom information spreadsheet so that a heuristic file can be written. Users should specify a subject with all scans of interest present, and run this command on all sessions of interest. """
    config: ProjectOptions = load_project_config(config_file)

    heuristic_file = resource_filename(__name__, 'data/setup_heuristic.py')

    if session:
        heudiconv_string = '''module add heudiconv \n heudiconv -d {dicomdirectory} -s {subject} '''\
        ''' -ss {sess} -f {heuristic} -o ./test/ -b --minmeta \n cp ./test/'''\
        '''.heudiconv/{subject}/ses-{sess}/info/dicominfo_ses-{sess}.tsv {outputfile} \n rm -rf ./test/'''
    else:
        heudiconv_string = '''module add heudiconv \n heudiconv -d {dicomdirectory} -s {subject} ''' \
                           ''' -f {heuristic} -o ./test/ -b --minmeta \n cp ./test/''' \
                           '''.heudiconv/{subject}/info/dicominfo.tsv {outputfile} \n rm -rf ./test/'''

    batch_manager = BatchManager(config.batch_config_path, None)
    batch_manager.update_time('1:0:0')
    batch_manager.update_mem_usage('3000')
    if session:
        job1 = Job("heudiconv_setup", heudiconv_string.format(
            dicomdirectory=os.path.abspath(dicom_directory),
            subject=subject,
            sess=session,
            heuristic = heuristic_file,
            outputfile = os.path.abspath(output_file),
        ))
    else:
        job1 = Job("heudiconv_setup", heudiconv_string.format(
            dicomdirectory=os.path.abspath(dicom_directory),
            subject=subject,
            heuristic = heuristic_file,
            outputfile = os.path.abspath(output_file),
        ))

    batch_manager.addjob(job1)
    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()
