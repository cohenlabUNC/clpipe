import sys
import os
import logging
import warnings
from pathlib import Path

# This hides a pybids future warning
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    from bids import BIDSLayout, BIDSLayoutIndexer, config as bids_config

from .config_json_parser import ClpipeConfigParser, GLMConfigParser
from .batch_manager import BatchManager, Job
from nipype.utils.filemanip import split_filename
from .postprocutils.workflows import build_postprocessing_workflow, build_confound_postprocessing_workflow
from .error_handler import exception_handler
from .errors import *

"""
Controller Functions - Serve as a middle layer between the front-end (CLI) and distribution / workflow setup functions. Handles sanitization, 
    configuration parsing, batch manager initialization, and is the last layer of exception catching

    - postprocess_subjects_controller
    - postprocess_subject_controller
    - postprocess_image_controller

Distributor Functions - Create and submit child job processes
    - distribute_subject_jobs
    - distribute_image_jobs

Workflow Builder & Runner - handles the creation and running of an image processing workflow
    - build_and_run_image_workflow
"""

def postprocess_subjects_controller(subjects=None, config_file=None, bids_dir=None, fmriprep_dir=None, output_dir=None, 
    batch=False, submit=False, log_dir=None, pybids_db_path=None, refresh_index=False, debug=False):

    config = _parse_config(config_file)
    config_file = Path(config_file)

    if not fmriprep_dir:
        fmriprep_dir = Path(config["FMRIPrepOptions"]["OutputDirectory"]) / "fmriprep"
    fmriprep_dir = Path(fmriprep_dir)

    if not bids_dir:
        bids_dir = Path(config["FMRIPrepOptions"]["BIDSDirectory"])
    bids_dir = Path(bids_dir)

    if not output_dir:
        output_dir = Path(config["ProjectDirectory"]) / "data_postproc2"
    output_dir = Path(output_dir)

    if not log_dir:
        log_dir = Path(config["ProjectDirectory"]) / "logs" / "postproc2_logs"
    log_dir = Path(log_dir)

    if not pybids_db_path:
        pybids_db_path = Path(config["ProjectDirectory"]) / "bids_index"
    pybids_db_path = Path(pybids_db_path)

    logger = _get_logger("postprocess_subjects_controller")

    # Setup Logging
    if debug: 
        logger.setLevel(logging.DEBUG)
    else:
        sys.excepthook = exception_handler
    logger.info(f"Preparing postprocessing job targeting: {str(fmriprep_dir)}")

    # Setup batch jobs if indicated
    batch_manager = None
    if batch:
        slurm_log_dir = log_dir / "slurm_out"
        if not slurm_log_dir.exists():
            logger.info(f"Creating slurm log directory: {slurm_log_dir}")
            slurm_log_dir.mkdir(exist_ok=True, parents=True)
        batch_manager = _setup_batch_manager(config, slurm_log_dir, non_processing=True)

    # Create jobs based on subjects given for processing
    # TODO: PYBIDS_DB_PATH should have config arg
    try:
        distribute_subject_jobs(bids_dir, fmriprep_dir, output_dir, config_file, submit=submit, batch_manager=batch_manager,
            subjects_to_process=subjects, log_dir=log_dir, pybids_db_path=pybids_db_path, 
            refresh_index=refresh_index)
    except NoSubjectsFoundError:
        sys.exit()
    except FileNotFoundError:
        sys.exit()

    sys.exit()


def postprocess_subject_controller(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, batch, submit, log_dir):
    logger = _get_logger("postprocess_subject_controller")
    
    logger.info(f"Processing subject: {subject_id}")

    config = _parse_config(config_file)
    config_file = Path(config_file)
    
    postprocessing_config = config["PostProcessingOptions2"]

    batch_manager = None
    if batch:
        slurm_log_dir = log_dir / Path(f"sub-{subject_id}") / "slurm_out"
        if not slurm_log_dir.exists():
            logger.info(f"Creating subject slurm log directory: {slurm_log_dir}")
            slurm_log_dir.mkdir(exist_ok=True, parents=True)
        batch_manager = _setup_batch_manager(config, slurm_log_dir)

    try:
        distribute_image_jobs(subject_id, bids_dir, fmriprep_dir, output_dir, postprocessing_config, config_file, pybids_db_path=index_dir, submit=submit,
            batch_manager=batch_manager, log_dir=log_dir)
    except SubjectNotFoundError:
        sys.exit()
    except ValueError:
        sys.exit()
    except FileNotFoundError:
        sys.exit()
    
    sys.exit()


def postprocess_image_controller(config_file, subject_id, task, run, image_space, image_path, bids_dir, fmriprep_dir, 
    pybids_db_path, subject_out_dir, working_dir, log_dir):

    logger = _get_logger("postprocess_image_controller")

    logger.info(f"Processing image: {image_path}")

    config = _parse_config(config_file)
    config_file = Path(config_file)

    postprocessing_config = config["PostProcessingOptions2"]

    build_and_run_image_workflow(postprocessing_config, subject_id, task, run, image_space, image_path, bids_dir, fmriprep_dir, pybids_db_path,
        subject_out_dir, working_dir, log_dir)
   
    sys.exit()
    

def distribute_subject_jobs(bids_dir, fmriprep_dir, output_dir: os.PathLike, config_file: os.PathLike, submit=False, batch_manager=None,
        subjects_to_process=None, log_dir: os.PathLike=None, pybids_db_path: os.PathLike=None, refresh_index=False):

    logger = _get_logger("distribute_subject_jobs")
    _add_file_handler(logger, log_dir, 'postprocess.log')

    # Create the root output directory for all subject postprocessing results, if it doesn't yet exist.
    if not output_dir.exists():
        output_dir.mkdir()

    bids:BIDSLayout = _get_bids(bids_dir, database_path=pybids_db_path, fmriprep_dir=fmriprep_dir, refresh=refresh_index)

    subjects_to_process = _get_subjects(bids, subjects_to_process)

    submission_strings = _create_submission_strings(subjects_to_process, bids_dir, fmriprep_dir, config_file, pybids_db_path,
        output_dir, log_dir, logger, batch_manager, submit)
    
    _submit_jobs(batch_manager, submission_strings, logger, submit=submit)


def distribute_image_jobs(subject_id: str, bids_dir: os.PathLike, fmriprep_dir: os.PathLike, out_dir: os.PathLike, postprocessing_config: dict,
    config_file: os.PathLike, pybids_db_path: os.PathLike=None, submit=False, batch_manager=None, log_dir: os.PathLike=None):

    logger = _get_logger(f"distribute_image_jobs_sub-{subject_id}")
    
    bids_dir = Path(bids_dir)
    pybids_db_path = Path(pybids_db_path)
    fmriprep_dir = Path(fmriprep_dir)
    log_dir=Path(log_dir)
    out_dir = Path(out_dir)
    config_file = Path(config_file)
    
    # Create a subject folder for this subject's postprocessing output, if one doesn't already exist
    subject_out_dir = out_dir / ("sub-" + subject_id) / "func"
    if not subject_out_dir.exists():
        logger.info(f"Creating subject directory: {subject_out_dir}")
        subject_out_dir.mkdir(exist_ok=True, parents=True)

    # If no top-level working directory is provided, make one in the out_dir
    working_dir = postprocessing_config["WorkingDirectory"]
    if not working_dir:
        subject_working_dir = out_dir / "working" / ("sub-" + subject_id)
    # Otherwise, use the provided top-level directory as a base, and name working directory after the subject
    else:
        subject_working_dir = Path(working_dir) / ("sub-" + subject_id) 
    
    # Create the working directory, if it doesn't exist
    if not subject_working_dir.exists():
        logger.info(f"Creating subject working directory: {subject_working_dir}")
        subject_working_dir.mkdir(exist_ok=True, parents=True)

    # Create a postprocessing logging directory for this subject, if it doesn't exist
    log_dir = log_dir / ("sub-" + subject_id)
    if not log_dir.exists():
        logger.info(f"Creating subject log directory: {log_dir}")
        log_dir.mkdir(exist_ok=True)
    _add_file_handler(logger, log_dir, f'sub-{subject_id}.log')

    bids:BIDSLayout = _get_bids(bids_dir, database_path=pybids_db_path, fmriprep_dir=fmriprep_dir)
    _validate_subject_exists(bids, subject_id, logger)

    submission_strings = _create_image_submission_strings(subject_id, bids, bids_dir, fmriprep_dir, pybids_db_path, 
        subject_out_dir, working_dir, postprocessing_config, config_file, log_dir, logger)

    _submit_jobs(batch_manager, submission_strings, logger, submit=submit)


def build_and_run_image_workflow(postprocessing_config, subject_id, task, run, image_space, image_path, bids_dir, fmriprep_dir, 
    pybids_db_path, subject_out_dir, working_dir, log_dir):
    
    image_path = Path(image_path)
    working_dir = Path(working_dir)
    log_dir = Path(log_dir)
    subject_out_dir = Path(subject_out_dir)

    image_file_name = image_path.stem

    name = f"subject_{subject_id}_task_{task}"
    if run: name += f"_run_{run}"

    logger = _get_logger(f"postprocess_image_{name}")

    bids:BIDSLayout = _get_bids(bids_dir, database_path=pybids_db_path, fmriprep_dir=fmriprep_dir)

    mixing_file, noise_file = None, None
    if "AROMARegression" in postprocessing_config["ProcessingSteps"]:
        try:
            mixing_file = _get_mixing_file(bids, subject_id, task, run, logger)
            noise_file = _get_noise_file(bids, subject_id, task, run, logger)
        except MixingFileNotFoundError as mfnfe:
            logger.error(mfnfe)
            sys.exit(1)
        except NoiseFileNotFoundError as nfnfe:
            logger.error(nfnfe)
            sys.exit(1)

def _get_mixing_file(bids, subject_id, task, run, logger):
    logger.info("Searching for MELODIC mixing file")
    try:
        mixing_file = bids.get(
            subject=subject_id, task=task, run=run, suffix="mixing", extension=".tsv", return_type="filename",
                desc="MELODIC", scope="derivatives"
        )[0]
        logger.info(f"MELODIC mixing file found: {mixing_file}")

        return mixing_file
    except IndexError:
        raise MixingFileNotFoundError(f"MELODIC mixing file for sub-{subject_id} task-{task} not found.")

def _get_noise_file(bids, subject_id, task, run, logger):
    logger.info("Searching for AROMA noise ICs file")
    try:
        noise_file = bids.get(
            subject=subject_id, task=task, run=run, suffix="AROMAnoiseICs", extension=".csv", return_type="filename",
                scope="derivatives"
        )[0]
        logger.info(f"AROMA noise ICs file found: {noise_file}")
    except IndexError:
        raise NoiseFileNotFoundError(f"AROMA noise ICs file for sub-{subject_id} task-{task} not found.")


def _submit_jobs(batch_manager, submission_strings, logger, submit=True):
    num_jobs = len(submission_strings)

    if batch_manager:
        _populate_batch_manager(batch_manager, submission_strings, logger)
        if submit:
            logger.info(f"Running {num_jobs} job(s) in batch mode")
            batch_manager.submit_jobs()
        else:
            batch_manager.print_jobs()
    else:
        if submit:
            for key in submission_strings.keys():
                os.system(submission_strings[key])
        else:
            for key in submission_strings.keys():
                print(submission_strings[key])


def _create_image_submission_strings(subject_id, bids, bids_dir, fmriprep_dir, pybids_db_path, subject_out_dir, working_dir, postprocessing_config, config_file, log_dir, logger):
    logger.info(f"Searching for images to process")
    
    # Find the subject's images to run post_proc on
    try:
        image_space = postprocessing_config["TargetImageSpace"]
        logger.info(f"Target image space: {image_space}")

        images_to_process = bids.get(
            subject=subject_id, extension="nii.gz", datatype="func", 
            suffix="bold", desc="preproc", scope="derivatives", space=image_space)

        if len(images_to_process) == 0:
            raise NoImagesFoundError(f"No preproc BOLD images found for sub-{subject_id} in space {image_space}.")

        logger.info(f"Found images: {len(images_to_process)}")
        logger.info(f"Building image jobs")

        submission_strings = {}
        SUBMISSION_STRING_TEMPLATE = ("postprocess_image {config_file} {subject_id} {task} {image_space} "
            "{image_path} {bids_dir} {fmriprep_dir} {pybids_db_path} {subject_out_dir} {working_dir} {log_dir} {run}")
        
        logger.info("Creating submission strings")
        for image in images_to_process:
            image_entities = image.get_entities()
            task = image_entities['task']
            try:
                run = f"-run {image_entities['run']}"
            except KeyError:
                run = ""

            key = f"Postprocessing_{str(Path(image.path).stem)}"
            
            submission_strings[key] = SUBMISSION_STRING_TEMPLATE.format(config_file=config_file,
                                                            subject_id=subject_id,
                                                            task=task,
                                                            run=run,
                                                            image_space=image_space,
                                                            image_path=image.path,
                                                            bids_dir=bids_dir,
                                                            fmriprep_dir=fmriprep_dir,
                                                            pybids_db_path=pybids_db_path,
                                                            subject_out_dir=subject_out_dir,
                                                            working_dir=working_dir,
                                                            log_dir=log_dir)
        return submission_strings

    except IndexError:
        raise NoImagesFoundError(f"No preproc BOLD image for subject {subject_id} found.")


def _validate_subject_exists(bids, subject_id, logger):
    # Open the bids dir and validate that it contains the subject
    logger.info(f"Checking for requested subject in fmriprep output")
    if len(bids.get(subject=subject_id, scope="derivatives")) == 0:
        snfe = f"Subject {subject_id} was not found in fmriprep output. You may need to add the option '-refresh_index' if this is a new subject."
        logger.error(snfe)
        raise SubjectNotFoundError(snfe)
    

def _parse_config(config_file):
    # Get postprocessing configuration from general config
    if not config_file:
        raise ValueError("No config file provided")
    
    configParser = ClpipeConfigParser()
    configParser.config_updater(config_file)
    config = configParser.config

    return config

def _get_bids(bids_dir: os.PathLike, validate=False, database_path: os.PathLike=None, fmriprep_dir: os.PathLike=None, 
                index_metadata=False, refresh=False, logger=None) -> BIDSLayout:
    try:
        database_path = Path(database_path)
        
        # Use an existing pybids database, and user did not request an index refresh
        if database_path.exists() and not refresh:
            if logger:
                logger.info(f"Using existing BIDS index: {database_path}")
            return BIDSLayout(database_path=database_path)
        # Index from scratch (slow)
        else:
            indexer = BIDSLayoutIndexer(validate=validate, index_metadata=index_metadata)
            if logger:
                logger.info(f"Indexing BIDS directory: {bids_dir}")
            print("Indexing BIDS directory - this can take a few minutes...")

            if fmriprep_dir:
                return BIDSLayout(bids_dir, validate=validate, indexer=indexer, database_path=database_path, derivatives=fmriprep_dir, reset_database=refresh)
            else:
                return BIDSLayout(bids_dir, validate=validate, indexer=indexer, database_path=database_path, reset_database=refresh)
    except FileNotFoundError as fne:
        if logger:
            logger.error(fne)
        raise fne


def _get_subjects(bids_dir: BIDSLayout, subjects):   
    # If no subjects were provided, use all subjects in the fmriprep directory
    if subjects is None or len(subjects) == 0:
        subjects = bids_dir.get_subjects(scope='derivatives')
        if len(subjects) == 0:
            no_subjects_found_str = f"No subjects found to parse at: {bids_dir.root}"
            raise NoSubjectsFoundError(no_subjects_found_str)

    return subjects


def _populate_batch_manager(batch_manager, submission_strings, logger):
    logger.info("Setting up batch manager with jobs to run.")

    for key in submission_strings.keys():
        batch_manager.addjob(Job(key, submission_strings[key]))

    batch_manager.createsubmissionhead()
    batch_manager.compilejobstrings()


def _setup_batch_manager(config, log_dir, non_processing=False):
    batch_manager = BatchManager(config['BatchConfig'], log_dir)
    batch_manager.update_mem_usage(config['PostProcessingOptions2']['BatchOptions']['MemoryUsage'])
    batch_manager.update_time(config['PostProcessingOptions2']['BatchOptions']['TimeUsage'])
    batch_manager.update_nthreads(config['PostProcessingOptions2']['BatchOptions']['NThreads'])
    batch_manager.update_email(config["EmailAddress"])

    if non_processing:
        batch_manager.update_mem_usage(2000)
        batch_manager.update_nthreads(1)
        batch_manager.update_time("0:0:30")

    return batch_manager


def _create_submission_strings(subjects_to_process, 
    bids_dir, fmriprep_dir, config_file, pybids_db_path, output_dir, log_dir, logger, batch_manager, submit):
    
    logger.info("Creating submission strings")
    submission_strings = {}

    batch_flag = ""
    submit_flag = ""
    if not batch_manager:
        batch_flag = "-no-batch"
    if submit:
        submit_flag = "-submit"

    SUBMISSION_STRING_TEMPLATE = """postprocess_subject {subject_id} {bids_dir} {fmriprep_dir} {output_dir} {config_file} {index_dir} {log_dir} {batch} {submit}"""
    for subject in subjects_to_process:
        key = "Postprocessing_sub-" + subject
        submission_strings[key] = SUBMISSION_STRING_TEMPLATE.format(subject_id=subject,
                                                        bids_dir=bids_dir,
                                                        fmriprep_dir=fmriprep_dir,
                                                        config_file=config_file,
                                                        index_dir=pybids_db_path,
                                                        output_dir=output_dir,
                                                        log_dir=log_dir,
                                                        batch=batch_flag,
                                                        submit=submit_flag)
    return submission_strings


def _get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create log handler
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)

    # Create log formatter to add to handler
    c_format = logging.Formatter('%(asctime)s - %(levelname)s: %(name)s - %(message)s')
    c_handler.setFormatter(c_format)
    
    # Add handler to logger
    logger.addHandler(c_handler)

    return logger


def _add_file_handler(logger, log_dir, f_name):
    # Create log handler
    f_handler = logging.FileHandler(log_dir / f_name)
    f_handler.setLevel(logging.DEBUG)
    
    # Create log format
    f_format = logging.Formatter('%(asctime)s - %(levelname)s: %(name)s - %(message)s')
    f_handler.setFormatter(f_format)

    # Add handler to the logger
    logger.addHandler(f_handler)
