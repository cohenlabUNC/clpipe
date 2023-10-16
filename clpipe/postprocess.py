"""Postprocessing Pipeline Workflow Builder and Distributer.

Based on user input, builds and runs a postprocessing pipeline for a set 
of subjects, distributing the workload across a cluster if requested.
"""

import sys
import os
import warnings
import json
import time
from pathlib import Path

from .bids import (
    get_bids,
    get_confounds,
    get_images_to_process,
    get_mask,
    get_mixing_file,
    get_noise_file,
    get_subjects,
    get_tr,
    validate_subject_exists,
)
import nipype.pipeline.engine as pe

# This hides a pybids future warning
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    from bids import BIDSLayout
    from bids.layout import BIDSFile

from .config.options import (
    ProjectOptions,
    PostProcessingRunConfig,
    DEFAULT_WORKING_DIRECTORY,
)
from .config.options import DEFAULT_PROCESSING_STREAM
from .batch_manager import BatchManager, Job
from .postprocutils.global_workflows import build_postprocessing_wf
from .postprocutils.utils import draw_graph
from .utils import get_logger, resolve_fmriprep_dir
from .errors import *

STEP_NAME = "postprocess"
PROCESSING_DESCRIPTION_FILE_NAME = "processing_description.json"
IMAGE_TIME_DIMENSION_INDEX = 3
IMAGE_SUBMISSION_STRING_TEMPLATE = (
    "postprocess_image {run_config_file} "
    "{image_file} {subject_out_dir} {subject_working_dir} {subject_log_dir} "
    "{debug}"
)
BIDS_INDEX_NAME = "bids_index"
"""This is the location of the pybids-generated index"""

SUBJECT_LOG_DIR = "distributor"
"""Where to save batch files, within the postprocessing log folder, for subject-level batch logs"""
RUN_CONFIG_FILE_NAME = "run_config.json"


def postprocess_subjects(
    subjects=None,
    config_file=None,
    bids_dir=None,
    fmriprep_dir=None,
    output_dir=None,
    processing_stream=DEFAULT_PROCESSING_STREAM,
    batch=False,
    submit=False,
    log_dir=None,
    pybids_db_path=None,
    refresh_index=False,
    debug=False,
    cache=True,
):
    """
    Parse configuration and sanitize inputs in preparation for
        subject job distribution.
    """

    options: ProjectOptions = ProjectOptions.load(config_file)
    options.fmriprep.load_cli_args(
        bids_directory=bids_dir,
    )
    options.postprocessing.load_cli_args(
        output_directory=output_dir,
        target_directory=fmriprep_dir,
        log_directory=log_dir,
    )
    if options.postprocessing.working_directory == DEFAULT_WORKING_DIRECTORY:
        raise ValueError("No working directory specified.")
    if processing_stream is not DEFAULT_PROCESSING_STREAM:
        options.postprocessing = apply_stream(options, processing_stream)

    # Initialize the run config
    # TODO: The getters here are still a bit confusing and could be moved to run_config,
    #   handled internally
    run_config: PostProcessingRunConfig = PostProcessingRunConfig(
        options=options.postprocessing,
        target_directory=options.postprocessing.target_directory,
        bids_directory=options.fmriprep.bids_directory,
        batch_config_file=options.batch_config_path,
        email_address=options.email_address,
        stream_working_directory=options.postprocessing.get_stream_working_dir(
            processing_stream
        ),
        stream_log_directory=options.postprocessing.get_stream_log_dir(
            processing_stream
        ),
        stream_output_directory=options.postprocessing.get_stream_output_dir(
            processing_stream
        ),
        pybids_db_path=options.postprocessing.get_pybids_db_path(
            processing_stream, BIDS_INDEX_NAME
        ),
    )
    # This is the only run-related attribute that can be set by the CLI right now
    run_config.load_cli_args(pybids_db_path=pybids_db_path)

    # Setup top-level directories
    setup_dirs(run_config)

    # Save the run configuration for use downstream
    stream_run_config_path = (
        Path(run_config.stream_working_directory) / RUN_CONFIG_FILE_NAME
    )
    run_config.dump(stream_run_config_path)

    # Setup Logging
    logger = get_logger(STEP_NAME, debug=debug, log_dir=options.get_logs_dir())

    options.postprocessing.target_directory = resolve_fmriprep_dir(
        options.postprocessing.target_directory
    )
    logger.info(
        f"Preparing postprocessing job targeting: {options.postprocessing.target_directory}"
    )

    time.sleep(0.5)

    logger.info(f"Output directory: {options.postprocessing.output_directory}")

    # Check to make sure working directory has been changed from the default
    if (
        options.postprocessing.working_directory
        == ProjectOptions().postprocessing.working_directory
    ):
        logger.error(
            "A working directory for this step must be provided in your config file."
        )
        sys.exit(1)

    # Create jobs based on subjects given for processing
    try:
        bids: BIDSLayout = get_bids(
            options.fmriprep.bids_directory,
            database_path=run_config.pybids_db_path,
            logger=logger,
            fmriprep_dir=options.postprocessing.target_directory,
            refresh=refresh_index,
        )

        subjects_to_process = get_subjects(bids, subjects)
        logger.info(
            f"Processing requested for subject(s): {','.join(subjects_to_process)}"
        )
        time.sleep(0.5)

        for subject in subjects_to_process:
            postprocess_subject(
                subject_id=subject,
                run_config=run_config,
                run_config_path=stream_run_config_path,
                bids=bids,
                batch=batch,
                submit=submit,
                debug=debug,
            )

    except NoSubjectsFoundError as nsfe:
        logger.error(nsfe)
        sys.exit(1)
    except FileNotFoundError as fnfe:
        logger.error(fnfe)
        sys.exit(1)


def setup_dirs(run_config: PostProcessingRunConfig):
    os.makedirs(run_config.stream_output_directory, exist_ok=True)
    os.makedirs(run_config.stream_working_directory, exist_ok=True)
    os.makedirs(run_config.stream_log_directory, exist_ok=True)


def apply_stream(options, processing_stream):
    from dataclasses import replace

    stream_options = None
    for stream in options.processing_streams:
        if stream.stream_name == processing_stream:
            stream_options = stream.postprocessing_options
            break

    return replace(options.postprocessing, **stream_options)


def postprocess_subject(
    subject_id: str,
    run_config: PostProcessingRunConfig,
    run_config_path: str,
    bids: BIDSLayout,
    batch: bool = False,
    submit: bool = False,
    debug=False,
):
    """
    Handle postprocessing for a single subject.
    """

    sub_with_id = "sub-" + subject_id

    # Create a postprocessing logging directory for this subject,
    # if it doesn't exist
    subject_log_dir: Path = Path(run_config.stream_log_directory) / sub_with_id
    subject_log_dir.mkdir(exist_ok=True)

    logger = get_logger(
        f"postprocess_{sub_with_id}",
        log_dir=subject_log_dir,
        f_name=f"{sub_with_id}.log",
        debug=debug,
    )
    logger.info(f"Processing subject: {subject_id}")

    batch_manager = None
    if batch:
        subject_slurm_log_dir = subject_log_dir / "slurm_out"
        subject_slurm_log_dir.mkdir(exist_ok=True)
        batch_manager = _setup_batch_manager(run_config, subject_slurm_log_dir)

    try:
        logger.info(f"Checking for requested subject in fmriprep output")
        validate_subject_exists(bids, subject_id)

        try:
            tasks = run_config.options.target_tasks
        except KeyError:
            logger.warn(
                (
                    "Postprocessing configuration setting 'TargetTasks' not set. "
                    "Defaulting to all tasks."
                )
            )
            tasks = None
        try:
            acquisitions = run_config.options.target_acquisitions
        except KeyError:
            logger.warn(
                (
                    "Postprocessing configuration setting 'TargetAcquisitions' "
                    "not set. Defaulting to all acquisitions."
                )
            )
            acquisitions = None

        images_to_process = get_images_to_process(
            subject_id=subject_id,
            image_space=run_config.options.target_image_space,
            bids=bids,
            logger=logger,
            tasks=tasks,
            acquisitions=acquisitions,
        )

        subject_out_dir = Path(run_config.stream_output_directory) / sub_with_id
        subject_working_dir = Path(run_config.stream_working_directory) / sub_with_id

        if not subject_out_dir.exists():
            logger.info(f"Creating subject directory: {subject_out_dir}")
            subject_out_dir.mkdir(parents=True)

        if not subject_working_dir.exists():
            logger.info(f"Creating subject working directory: {subject_working_dir}")
            subject_working_dir.mkdir(parents=True, exist_ok=False)

        submission_strings = _create_image_submission_strings(
            run_config_path,
            images_to_process,
            subject_out_dir,
            subject_working_dir,
            subject_log_dir,
            debug,
            logger,
        )

        _submit_jobs(batch_manager, submission_strings, logger, submit=submit)
    except SubjectNotFoundError as snfe:
        logger.error(snfe)
    except ValueError as ve:
        logger.error(ve)
    except FileNotFoundError as fnfe:
        logger.error(fnfe)


def postprocess_image(
    run_config_file: os.PathLike,
    image_path: os.PathLike,
    subject_out_dir: os.PathLike,
    subject_working_dir: os.PathLike,
    subject_log_dir: os.PathLike,
    confounds_only=False,
    debug=False,
):
    """
    Setup the workflows specified in the postprocessing configuration.
    """
    image_path = Path(image_path)
    image_short_name = f"{str(Path(image_path).stem)}"

    run_config: PostProcessingRunConfig = PostProcessingRunConfig.load(run_config_file)

    logger = get_logger(
        "postprocess_image",
        log_dir=subject_log_dir,
        f_name=f"{image_short_name}.log",
        debug=debug,
    )
    logger.info(f"Processing image: {image_path}")

    # Grab only the image file name in a way that works
    #   on both .nii and .nii.gz
    file_name_no_extensions = Path(
        str(image_path).rstrip("".join(image_path.suffixes))
    ).stem
    # Remove modality to shorten necessary pipeline name
    file_name_no_modality = file_name_no_extensions.replace("_desc-preproc_bold", "")
    # Remove hyphens to allow use as a pipeline name
    pipeline_name = file_name_no_modality.replace("-", "_")

    bids: BIDSLayout = get_bids(
        run_config.bids_directory,
        database_path=run_config.pybids_db_path,
        fmriprep_dir=run_config.target_directory,
    )
    # Lookup the BIDSFile with the image path
    bids_image: BIDSFile = bids.get_file(image_path)
    # Fetch the image's entities
    image_entities = bids_image.get_entities()
    # Create a sub dict of the entities we will need to query on
    query_params = {
        k: image_entities[k]
        for k in image_entities.keys()
        & {"session", "subject", "task", "run", "acquisition", "space"}
    }
    # Create a specific dict for searching non-image files
    non_image_query_params = query_params.copy()
    non_image_query_params.pop("space")

    mixing_file, noise_file = None, None
    if "AROMARegression" in run_config.options.processing_steps:
        try:
            # TODO: update these for image entities
            mixing_file = get_mixing_file(bids, non_image_query_params, logger)
            noise_file = get_noise_file(bids, non_image_query_params, logger)
        except MixingFileNotFoundError as mfnfe:
            logger.error(mfnfe)
            # TODO: this should raise the error for the controller to handle
            sys.exit(1)
        except NoiseFileNotFoundError as nfnfe:
            logger.error(nfnfe)
            sys.exit(1)

    # Search for this subject's files necessary for processing
    mask_image = get_mask(bids, query_params, logger)
    tr = get_tr(bids, query_params, logger)
    confounds_path = get_confounds(bids, non_image_query_params, logger)

    # Try and build an export path for postprocess confounds if the subject has
    #   confounds to work with
    confounds_export_path = None
    if confounds_path is not None:
        try:
            confounds_export_path = build_export_path(
                confounds_path,
                query_params["subject"],
                run_config.target_directory,
                subject_out_dir,
            )
        except ValueError as ve:
            logger.warn(ve)
            logger.warn("Skipping confounds processing")

    # Build the image export path
    image_export_path = None
    if not confounds_only:
        image_export_path = build_export_path(
            image_path,
            query_params["subject"],
            run_config.target_directory,
            subject_out_dir,
        )

    # Build the global postprocessing workflow
    postproc_wf: pe.Workflow = build_postprocessing_wf(
        run_config.options,
        tr,
        name=pipeline_name,
        image_file=bids_image,
        image_export_path=image_export_path,
        confounds_file=confounds_path,
        confounds_export_path=confounds_export_path,
        working_dir=subject_working_dir,
        mask_file=mask_image,
        mixing_file=mixing_file,
        noise_file=noise_file,
        base_dir=subject_working_dir,
        crashdump_dir=subject_working_dir,
    )

    if run_config.options.write_process_graph:
        draw_graph(
            postproc_wf,
            "processing_graph",
            run_config.stream_output_directory,
            logger=logger,
        )

    postproc_wf.run()
    sys.exit(0)


def build_export_path(
    image_path: os.PathLike,
    subject_id: str,
    fmriprep_dir: os.PathLike,
    subject_out_dir: os.PathLike,
) -> Path:
    """Builds a new name for a processed image.

    Args:
        image_path (os.PathLike): The path to the original image file.
        subject_out_dir (os.PathLike): The destination directory.

    Returns:
        os.PathLike: Save path for an image file.
    """
    # Copy the directory structure following the subject-id
    # from the fmriprep dir
    out_path = Path(image_path).relative_to(Path(fmriprep_dir) / ("sub-" + subject_id))
    export_path = Path(subject_out_dir) / str(out_path)
    export_folder = export_path.parent

    # Create the output folder if it doesn't exist
    if not export_folder.exists():
        export_folder.mkdir(parents=True, exist_ok=True)

    export_path = Path(subject_out_dir) / str(out_path).replace("preproc", "postproc")
    print(f"Export path: {export_path}")

    return export_path


def _list_available_streams(postprocessing_config: dict):
    return postprocessing_config.keys()


def _write_processing_description_file(
    postprocessing_config: dict, processing_description_file: os.PathLike
):
    processing_steps = postprocessing_config["ProcessingSteps"]
    processing_step_options = postprocessing_config["ProcessingStepOptions"]
    processing_step_options_reference = processing_step_options.copy()
    confound_options = postprocessing_config["ConfoundOptions"]

    # Remove processing options not used
    for step_option in processing_step_options_reference.keys():
        if step_option not in processing_steps:
            processing_step_options.pop(step_option)

    # Write the processing file
    with open(processing_description_file, "w") as file_to_write:
        json.dump(postprocessing_config, file_to_write, indent=4)


def _get_processing_streams(options: ProjectOptions):
    # TODO: possible support for command showing processing streams
    pass


def _submit_jobs(batch_manager, submission_strings, logger, submit=True):
    num_jobs = len(submission_strings)

    if batch_manager:
        _populate_batch_manager(batch_manager, submission_strings, logger)
        if submit:
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


def _create_image_submission_strings(
    run_config_file,
    images_to_process,
    subject_out_dir,
    subject_working_dir,
    subject_log_dir,
    debug,
    logger,
):
    logger.info(f"Building image job submission strings")
    submission_strings = {}

    debug_flag = ""
    if debug:
        debug_flag = "-debug"

    logger.info("Creating submission string(s)")
    for image in images_to_process:
        key = f"{Path(image.path).stem}"

        submission_strings[key] = IMAGE_SUBMISSION_STRING_TEMPLATE.format(
            run_config_file=str(run_config_file),
            image_file=image.path,
            subject_out_dir=str(subject_out_dir),
            subject_working_dir=str(subject_working_dir),
            subject_log_dir=str(subject_log_dir),
            debug=debug_flag,
        )
        logger.debug(submission_strings[key])
    return submission_strings


def _populate_batch_manager(batch_manager, submission_strings, logger):
    logger.info("Setting up batch manager with jobs to run.")

    for key in submission_strings.keys():
        batch_manager.addjob(Job(key, submission_strings[key]))

    batch_manager.createsubmissionhead()
    batch_manager.compilejobstrings()


def _setup_batch_manager(
    run_config: PostProcessingRunConfig, log_dir: str, non_processing=False
):
    batch_manager = BatchManager(run_config.batch_config_file, log_dir)
    batch_manager.update_mem_usage(run_config.options.batch_options.memory_usage)
    batch_manager.update_time(run_config.options.batch_options.time_usage)
    batch_manager.update_nthreads(run_config.options.batch_options.n_threads)
    batch_manager.update_email(run_config.email_address)

    if non_processing:
        batch_manager.update_mem_usage(2000)
        batch_manager.update_nthreads(1)
        batch_manager.update_time("0:30:0")

    return batch_manager
