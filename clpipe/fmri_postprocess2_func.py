import sys
import os
import logging
import json
import warnings
from pathlib import Path

import click
with warnings.catch_warnings():
    # This hides a pybids future warning
    warnings.filterwarnings("ignore", category=FutureWarning)
    from bids import BIDSLayout, BIDSLayoutIndexer, config as bids_config

from .config_json_parser import ClpipeConfigParser, GLMConfigParser
from .batch_manager import BatchManager, Job
from nipype.utils.filemanip import split_filename
from .postprocutils.workflows import build_postprocessing_workflow, build_confound_postprocessing_workflow
from .error_handler import exception_handler


logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

class NoSubjectTaskFoundError(ValueError):
    pass

class NoImagesFoundError(ValueError):
    pass

class NoSubjectsFoundError(ValueError):
    pass

class SubjectNotFoundError(ValueError):
    pass

class ConfoundsNotFoundError(ValueError):
    pass

class MixingFileNotFoundError(ValueError):
    pass

class NoiseFileNotFoundError(ValueError):
    pass

@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required=True,
              help='Use a given configuration file.')
@click.option('-fmriprep_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="""Which fmriprep directory to process. 
    If a configuration file is provided with a BIDS directory, this argument is not necessary. 
    Note, must point to the ``fmriprep`` directory, not its parent directory.""")
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False), default=None, required=False, help = """Where to put the postprocessed data. 
    If a configuration file is provided with a output directory, this argument is not necessary.""")
@click.option('-log_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), default=None, required = False, help = 'Path to the logging directory.')
@click.option('-index_dir', type=click.Path(dir_okay=True, file_okay=False), default=None, required=False,
              help='Give the path to an existing pybids index database.')
@click.option('-refresh_index', is_flag=True, default=False, required=False,
              help='Refresh the pybids index database to reflect new fmriprep artifacts.')
@click.option('-batch/-no-batch', is_flag = True, default=True, help = 'Flag to create batch jobs without prompt.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC without prompt.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess2_cli(subjects, config_file, fmriprep_dir, output_dir, batch, submit, log_dir, index_dir, refresh_index, debug):
    postprocess_fmriprep_dir(subjects=subjects, config_file=config_file, fmriprep_dir=fmriprep_dir, output_dir=output_dir, 
    batch=batch, submit=submit, log_dir=log_dir, pybids_db_path=index_dir, refresh_index=refresh_index, debug=debug)


@click.command()
@click.argument('subject_id')
@click.argument('bids_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('fmriprep_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('output_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('config_file', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('index_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('log_dir', type=click.Path(dir_okay=True, file_okay=False))
def postprocess_subject_cli(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, log_dir):
    postprocess_subject(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, log_dir)


def postprocess_subject(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, log_dir):
    click.echo(f"Processing subject: {subject_id}")
    
    try:
        job = PostProcessSubjectJob(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, pybids_db_path=index_dir, log_dir=log_dir)
        job()
    except SubjectNotFoundError:
        sys.exit()
    except ValueError:
        sys.exit()
    except FileNotFoundError:
        sys.exit()
    
    sys.exit()

def postprocess_fmriprep_dir(subjects=None, config_file=None, bids_dir=None, fmriprep_dir=None, output_dir=None, 
    batch=False, submit=False, log_dir=None, pybids_db_path=None, refresh_index=False, debug=False):

    config=None

    # Get postprocessing configuration from general config
    try:
        if not config_file:
            raise ValueError("No config file provided")
        else:
            configParser = ClpipeConfigParser()
            configParser.config_updater(config_file)
            config = configParser.config
            config_file = Path(config_file)
    except ValueError:
        sys.exit()

    if fmriprep_dir:
        fmriprep_dir = Path(fmriprep_dir)
    else:
        fmriprep_dir = Path(config["FMRIPrepOptions"]["OutputDirectory"]) / "fmriprep"

    if bids_dir:
        bids_dir = Path(bids_dir)
    else:
        bids_dir = Path(config["FMRIPrepOptions"]["BIDSDirectory"])

    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = Path(config["ProjectDirectory"]) / "data_postproc2"

    if log_dir:
        log_dir = Path(log_dir)
    else:
        log_dir = Path(config["ProjectDirectory"]) / "logs" / "postproc2_logs"

    if pybids_db_path:
        pybids_db_path = Path(pybids_db_path)
    else:
        pybids_db_path = Path(config["ProjectDirectory"]) / "bids_index"

    slurm_log_dir = log_dir / "slurm_out"
    if not slurm_log_dir.exists():
            LOG.info(f"Creating subject working directory: {slurm_log_dir}")
            slurm_log_dir.mkdir(exist_ok=True, parents=True)

    # Setup Logging
    if debug: 
        LOG.setLevel(logging.DEBUG)
    else:
        sys.excepthook = exception_handler
    LOG.debug(f"Preparing postprocessing job targeting: {str(fmriprep_dir)}")
    click.echo(f"Preparing postprocessing job targeting: {str(fmriprep_dir)}")

    # Setup batch jobs if indicated
    if batch:
        batch_manager = _setup_batch_manager(config, slurm_log_dir)
    else:
        batch_manager = None

    # Create jobs based on subjects given for processing
    # TODO: PYBIDS_DB_PATH should have config arg
    try:
        process_subjects(bids_dir, fmriprep_dir, output_dir, config_file, submit=submit, batch_manager=batch_manager,
            subjects_to_process=subjects, log_dir=log_dir, pybids_db_path=pybids_db_path, 
            refresh_index=refresh_index)
    except NoSubjectsFoundError:
        sys.exit()
    except FileNotFoundError:
        sys.exit()

    sys.exit()

def process_subjects(bids_dir, fmriprep_dir, output_dir: os.PathLike, config_file: os.PathLike, submit=False, batch_manager=None,
        subjects_to_process=None, log_dir: os.PathLike=None, pybids_db_path: os.PathLike=None, refresh_index=False):

    logger = _get_logger("process_subjects")
    _add_file_handler(logger, log_dir)

    # Create the root output directory for all subject postprocessing results, if it doesn't yet exist.
    if not output_dir.exists():
        output_dir.mkdir()

    bids:BIDSLayout = _get_bids(bids_dir, database_path=pybids_db_path, fmriprep_dir=fmriprep_dir, refresh=refresh_index)

    subjects_to_process = _get_subjects(bids, subjects_to_process)

    num_jobs = len(subjects_to_process)
    submission_strings = _create_submission_strings(subjects_to_process, bids_dir, fmriprep_dir, config_file, pybids_db_path,
        output_dir, log_dir, logger)

    if batch_manager:
        _populate_batch_manager(batch_manager, submission_strings, logger)
        if submit:
            logger.info(f"Running {num_jobs} postprocessing jobs in batch mode")
            batch_manager.submit_jobs()
        else:
            batch_manager.print_jobs()
    else:
        if submit:
            for subject in submission_strings.keys():
                os.system(f"{submission_strings[subject]} &")
        else:
            for subject in submission_strings.keys():
                print(submission_strings[subject])


def _setup_batch_manager(config, log_dir):
    batch_manager = BatchManager(config['BatchConfig'], log_dir)
    batch_manager.update_mem_usage(config['PostProcessingOptions2']['BatchOptions']['MemoryUsage'])
    batch_manager.update_time(config['PostProcessingOptions2']['BatchOptions']['TimeUsage'])
    batch_manager.update_nthreads(config['PostProcessingOptions2']['BatchOptions']['NThreads'])
    batch_manager.update_email(config["EmailAddress"])

    return batch_manager

def _get_bids(bids_dir: os.PathLike, validate=False, database_path: os.PathLike=None, fmriprep_dir: os.PathLike=None, 
                index_metadata=False, refresh=False) -> BIDSLayout:
    try:
        database_path = Path(database_path)
        
        # Use an existing pybids database, and user did not request an index refresh
        if database_path.exists() and not refresh:
            LOG.info(f"Using existing BIDS index: {database_path}")
            return BIDSLayout(database_path=database_path)
        # Index from scratch (slow)
        else:
            indexer = BIDSLayoutIndexer(validate=validate, index_metadata=index_metadata)
            LOG.info(f"Indexing BIDS directory: {bids_dir}")
            print("Indexing BIDS directory - this can take a few minutes...")

            if fmriprep_dir:
                return BIDSLayout(bids_dir, validate=validate, indexer=indexer, database_path=database_path, derivatives=fmriprep_dir, reset_database=refresh)
            else:
                return BIDSLayout(bids_dir, validate=validate, indexer=indexer, database_path=database_path, reset_database=refresh)
    except FileNotFoundError as fne:
        LOG.error(fne)
        raise fne

def _get_subjects(bids_dir: BIDSLayout, subjects):   
    # If no subjects were provided, use all subjects in the fmriprep directory
    if subjects is None or len(subjects) == 0:
        subjects = bids_dir.get_subjects(scope='derivatives')
        if len(subjects) == 0:
            no_subjects_found_str = f"No subjects found to parse at: {bids_dir.root}"
            LOG.error(no_subjects_found_str)
            raise NoSubjectsFoundError(no_subjects_found_str)

    return subjects

def _populate_batch_manager(batch_manager, submission_strings, logger):
    logger.info("Setting up batch manager with jobs to run.")

    for subject in submission_strings.keys():
        batch_manager.addjob(Job("PostProcessing_sub-" + subject, submission_strings[subject]))

    batch_manager.createsubmissionhead()
    batch_manager.compilejobstrings()

def _setup_batch_manager(config, log_dir):
    batch_manager = BatchManager(config['BatchConfig'], log_dir)
    batch_manager.update_mem_usage(config['PostProcessingOptions2']['BatchOptions']['MemoryUsage'])
    batch_manager.update_time(config['PostProcessingOptions2']['BatchOptions']['TimeUsage'])
    batch_manager.update_nthreads(config['PostProcessingOptions2']['BatchOptions']['NThreads'])
    batch_manager.update_email(config["EmailAddress"])

    return batch_manager

def _create_submission_strings(subjects_to_process, 
    bids_dir, fmriprep_dir, config_file, pybids_db_path, output_dir, log_dir, logger):
    
    logger.info("Creating submission strings")
    submission_strings = {}

    submission_string_template = """postprocess_subject {subject_id} {bids_dir} {fmriprep_dir} {output_dir} {config_file} {index_dir} {log_dir}"""
    for subject in subjects_to_process:
        submission_strings[subject] = submission_string_template.format(subject_id=subject,
                                                        bids_dir=bids_dir,
                                                        fmriprep_dir=fmriprep_dir,
                                                        config_file=config_file,
                                                        index_dir=pybids_db_path,
                                                        output_dir=output_dir,
                                                        log_dir=log_dir)
    return submission_strings

def _get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create log handler
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)

    # Create log formatter to add to handler
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    
    # Add handler to logger
    logger.addHandler(c_handler)

    return logger

def _add_file_handler(logger, log_dir):
    # Create log handler
    f_handler = logging.FileHandler(log_dir / f'postprocess.log')
    f_handler.setLevel(logging.DEBUG)
    
    # Create log format
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)

    # Add handler to the logger
    logger.addHandler(f_handler)
        
