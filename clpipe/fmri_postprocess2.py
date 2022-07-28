"""Postprocessing Pipeline Workflow Builder and Distributer.

Based on user input, builds and runs a postprocessing pipeline for a set of subjects, distributing the workload across a cluster if requested.

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

import sys
import os
import logging
import warnings
import json
import click
from pathlib import Path

import pydantic
#from nilearn import plotting
#from nilearn.image import load_img, index_img

# This hides a pybids future warning
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    from bids import BIDSLayout, BIDSLayoutIndexer, config as bids_config
    from bids.layout import BIDSFile

from .config_json_parser import ClpipeConfigParser
from .batch_manager import BatchManager, Job
import nipype.pipeline.engine as pe
from .postprocutils.workflows import build_image_postprocessing_workflow, build_postprocessing_workflow
from .postprocutils.confounds_workflows import build_confounds_processing_workflow
from .error_handler import exception_handler
from .errors import *
from .cli import cli

DEFAULT_LOG_FILE_NAME = "postprocess.log"
DEFAULT_PROCESSING_STREAM_NAME = "smooth-filter-normalize"
PROCESSING_DESCRIPTION_FILE_NAME = "processing_description.json"
IMAGE_TIME_DIMENSION_INDEX = 3


@cli.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required=True,
              help='Use a given configuration file.')
@click.option('-fmriprep_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="""Which fmriprep directory to process. 
    If a configuration file is provided with a BIDS directory, this argument is not necessary. 
    Note, must point to the ``fmriprep`` directory, not its parent directory.""")
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False), default=None, required=False, help = """Where to put the postprocessed data. 
    If a configuration file is provided with a output directory, this argument is not necessary.""")
@click.option('-processing_stream', default=DEFAULT_PROCESSING_STREAM_NAME, required=False, help="Specify a processing stream to use defined in your configuration file.")
@click.option('-log_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), default=None, required = False, help = 'Path to the logging directory.')
@click.option('-index_dir', type=click.Path(dir_okay=True, file_okay=False), default=None, required=False,
              help='Give the path to an existing pybids index database.')
@click.option('-refresh_index', is_flag=True, default=False, required=False,
              help='Refresh the pybids index database to reflect new fmriprep artifacts.')
@click.option('-batch/-no-batch', is_flag = True, default=True, help = 'Flag to create batch jobs without prompt.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC without prompt.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess2(subjects, config_file, fmriprep_dir, output_dir, 
                      processing_stream, batch, submit, log_dir, index_dir, 
                      refresh_index, debug):
    """Perform additional processing on fMRIPrepped data"""

    postprocess_subjects_controller(
        subjects=subjects, config_file=config_file,fmriprep_dir=fmriprep_dir, 
        output_dir=output_dir, processing_stream=processing_stream,
        batch=batch, submit=submit, log_dir=log_dir, pybids_db_path=index_dir,
        refresh_index=refresh_index, debug=debug)


@click.command()
@click.argument('subject_id')
@click.argument('bids_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('fmriprep_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('output_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('processing_stream', default=DEFAULT_PROCESSING_STREAM_NAME)
@click.argument('config_file', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('index_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-batch/-no-batch', is_flag = True, default=True, help = 'Flag to create batch jobs without prompt.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC without prompt.')
@click.argument('log_dir', type=click.Path(dir_okay=True, file_okay=False))
def postprocess_subject_cli(subject_id, bids_dir, fmriprep_dir, output_dir, 
                            processing_stream, config_file, index_dir, 
                            batch, submit, log_dir):
    
    postprocess_subject_controller(
        subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, 
        batch, submit, log_dir, processing_stream=processing_stream)


@click.command()
@click.argument('config_file', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('image_path', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('bids_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('fmriprep_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('index_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('out_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('subject_out_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('processing_stream', default=DEFAULT_PROCESSING_STREAM_NAME)
@click.argument('subject_working_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('log_dir', type=click.Path(dir_okay=True, file_okay=False))
def postprocess_image_cli(config_file, image_path, bids_dir, fmriprep_dir, 
                          index_dir, out_dir, subject_out_dir, 
                          processing_stream, subject_working_dir, log_dir):
    
    postprocess_image_controller(
        config_file, image_path, bids_dir, fmriprep_dir, index_dir, out_dir, 
        subject_out_dir, subject_working_dir, log_dir, 
        processing_stream=processing_stream)


def postprocess_subjects_controller(subjects=None, config_file=None, bids_dir=None, fmriprep_dir=None, output_dir=None, 
    processing_stream=DEFAULT_PROCESSING_STREAM_NAME, batch=False, submit=False, log_dir=None, pybids_db_path=None, refresh_index=False, debug=False):
    """
    Parse configuration and sanitize inputs in preparation for subject job distribution. 
    """

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
            refresh_index=refresh_index, processing_stream=processing_stream)
    except NoSubjectsFoundError as nsfe:
        logger.error(nsfe)
        sys.exit()
    except FileNotFoundError as fnfe:
        logger.error(fnfe)
        sys.exit()

    sys.exit()


def postprocess_subject_controller(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, batch, submit, 
    log_dir, processing_stream=DEFAULT_PROCESSING_STREAM_NAME):
    """
    Parse configuration and (TODO) sanitize inputs for image job distribution.
    """
    
    logger = _get_logger("postprocess_subject_controller")
    
    logger.info(f"Processing subject: {subject_id}")

    config = _parse_config(config_file)
    config_file = Path(config_file)

    postprocessing_config = _fetch_postprocessing_stream_config(config, output_dir, processing_stream=processing_stream)

    batch_manager = None
    if batch:
        slurm_log_dir = log_dir / Path(f"sub-{subject_id}") / "slurm_out"
        if not slurm_log_dir.exists():
            logger.info(f"Creating subject slurm log directory: {slurm_log_dir}")
            slurm_log_dir.mkdir(exist_ok=True, parents=True)
        batch_manager = _setup_batch_manager(config, slurm_log_dir)

    try:
        distribute_image_jobs(subject_id, bids_dir, fmriprep_dir, output_dir, postprocessing_config, config_file, 
            pybids_db_path=index_dir, submit=submit, batch_manager=batch_manager, log_dir=log_dir, processing_stream=processing_stream)
    except SubjectNotFoundError as snfe:
        logger.error(snfe)
        sys.exit()
    except ValueError as ve:
        logger.error(ve)
        sys.exit()
    except FileNotFoundError as fnfe:
        logger.error(fnfe)
        sys.exit()
    
    sys.exit()


def postprocess_image_controller(config_file, image_path, bids_dir, fmriprep_dir, 
    pybids_db_path, out_dir, subject_out_dir, subject_working_dir, log_dir, processing_stream=DEFAULT_PROCESSING_STREAM_NAME):
    """
    Parse configuration and (TODO) sanitize inputs for the workflow builder.
    """

    logger = _get_logger("postprocess_image_controller")

    logger.info(f"Processing image: {image_path}")

    config = _parse_config(config_file)
    config_file = Path(config_file)

    postprocessing_config = _fetch_postprocessing_stream_config(config, out_dir, processing_stream=processing_stream)

    stream_dir = Path(out_dir) / processing_stream

    build_and_run_postprocessing_workflow(postprocessing_config, image_path, bids_dir, fmriprep_dir, pybids_db_path,
        stream_dir, subject_out_dir, subject_working_dir, log_dir)
   
    sys.exit()


def distribute_subject_jobs(bids_dir, fmriprep_dir, output_dir: os.PathLike, config_file: os.PathLike, processing_stream:str=DEFAULT_PROCESSING_STREAM_NAME,
    submit=False, batch_manager=None,subjects_to_process=None, log_dir: os.PathLike=None, pybids_db_path: os.PathLike=None, refresh_index=False):
    """
    Prepare arguments to be passed to the subject submission string creator.
    """

    logger = _get_logger("distribute_subject_jobs")
    _add_file_handler(logger, log_dir, DEFAULT_LOG_FILE_NAME)

    output_dir = Path(output_dir)
    # Don't create any files/directories unless the user is submitting
    if submit:
        # Create the root output directory for all subject postprocessing results, if it doesn't yet exist.
        if not output_dir.exists():
            output_dir.mkdir()

    bids:BIDSLayout = _get_bids(bids_dir, database_path=pybids_db_path, fmriprep_dir=fmriprep_dir, refresh=refresh_index)

    subjects_to_process = _get_subjects(bids, subjects_to_process)

    submission_strings = _create_submission_strings(subjects_to_process, bids_dir, fmriprep_dir, config_file, pybids_db_path,
        output_dir, processing_stream, log_dir, logger, batch_manager, submit)
    
    _submit_jobs(batch_manager, submission_strings, logger, submit=submit)


def distribute_image_jobs(subject_id: str, bids_dir: os.PathLike, fmriprep_dir: os.PathLike, out_dir: os.PathLike, postprocessing_config: dict,
    config_file: os.PathLike, pybids_db_path: os.PathLike=None, submit=False, batch_manager=None, log_dir: os.PathLike=None, 
    processing_stream=DEFAULT_PROCESSING_STREAM_NAME):
    """
    Sanitize paramters before passing into image submission string creator.
    """

    logger = _get_logger(f"distribute_image_jobs_sub-{subject_id}")
    
    bids_dir = Path(bids_dir)
    pybids_db_path = Path(pybids_db_path)
    fmriprep_dir = Path(fmriprep_dir)
    log_dir=Path(log_dir)
    out_dir = Path(out_dir)
    config_file = Path(config_file)
    
    # Create a subject folder for this subject's postprocessing output, if one doesn't already exist
    subject_out_dir = out_dir / processing_stream / ("sub-" + subject_id)
    if not subject_out_dir.exists():
        logger.info(f"Creating subject directory: {subject_out_dir}")
        subject_out_dir.mkdir(exist_ok=True, parents=True)

    working_dir = postprocessing_config["WorkingDirectory"]
    subject_working_dir = _get_subject_working_dir(working_dir, out_dir, subject_id, processing_stream, logger) 
    
    # Create a postprocessing logging directory for this subject, if it doesn't exist
    log_dir = log_dir / ("sub-" + subject_id)
    if not log_dir.exists():
        logger.info(f"Creating subject log directory: {log_dir}")
        log_dir.mkdir(exist_ok=True)
    _add_file_handler(logger, log_dir, f'sub-{subject_id}.log')

    bids:BIDSLayout = _get_bids(bids_dir, database_path=pybids_db_path, fmriprep_dir=fmriprep_dir)
    _validate_subject_exists(bids, subject_id, logger)

    image_space = postprocessing_config["TargetImageSpace"]
    try:
        tasks = postprocessing_config["TargetTasks"]
    except KeyError:
        logger.warn("Postprocessing configuration setting 'TargetTasks' not set. Defaulting to all tasks.")
        tasks = None
    try:
        acquisitions = postprocessing_config["TargetAcquisitions"]
    except KeyError:
        logger.warn("Postprocessing configuration setting 'TargetAcquisitions' not set. Defaulting to all acquisitions.")
        acquisitions = None

    images_to_process = _get_images_to_process(subject_id, image_space, bids, logger, tasks=tasks, acquisitions=acquisitions)

    submission_strings = _create_image_submission_strings(images_to_process, bids_dir, fmriprep_dir, pybids_db_path, 
        out_dir, subject_out_dir, processing_stream, subject_working_dir, config_file, log_dir, logger)

    _submit_jobs(batch_manager, submission_strings, logger, submit=submit)


def build_and_run_postprocessing_workflow(postprocessing_config, image_path, bids_dir, fmriprep_dir, 
    pybids_db_path, stream_dir, subject_out_dir, subject_working_dir, log_dir, confounds_only=False):
    """
    Setup the workflows specified in the postprocessing configuration.
    """
    
    image_path = Path(image_path)
    subject_working_dir = Path(subject_working_dir)
    log_dir = Path(log_dir)
    subject_out_dir = Path(subject_out_dir)

    # Grab only the image file name in a way that works on both .nii and .nii.gz
    file_name_no_extensions = Path(str(image_path).rstrip(''.join(image_path.suffixes))).stem
    # Remove hyphens to allow use as a pipeline name
    pipeline_name = file_name_no_extensions.replace('-', "_")

    logger = _get_logger(f"postprocess_image_{file_name_no_extensions}")

    bids:BIDSLayout = _get_bids(bids_dir, database_path=pybids_db_path, fmriprep_dir=fmriprep_dir)
    # Lookup the BIDSFile with the image path
    bids_image:BIDSFile = bids.get_file(image_path)
    # Fetch the image's entities
    image_entities = bids_image.get_entities()
    # Create a sub dict of the entities we will need to query on
    query_params = {k: image_entities[k] for k in image_entities.keys() & {"session", "subject", "task", "run", "acquisition", "space"}}
    # Create a specific dict for searching non-image files
    non_image_query_params = query_params.copy()
    non_image_query_params.pop("space")

    mixing_file, noise_file = None, None
    if "AROMARegression" in postprocessing_config["ProcessingSteps"]:
        try:
            #TODO: update these for image entities
            mixing_file = _get_mixing_file(bids, non_image_query_params, logger)
            noise_file = _get_noise_file(bids, non_image_query_params, logger)
        except MixingFileNotFoundError as mfnfe:
            logger.error(mfnfe)
            #TODO: this should raise the error for the controller to handle
            sys.exit(1)
        except NoiseFileNotFoundError as nfnfe:
            logger.error(nfnfe)
            sys.exit(1)

    mask_image = _get_mask(bids, query_params, logger)
    tr = _get_tr(bids, query_params, logger)
    confounds_path = _get_confounds(bids, non_image_query_params, logger)

    image_wf = None
    confounds_wf = None

    if confounds_path is not None:
        try:
            confounds_export_path = _build_export_path(confounds_path, query_params["subject"], fmriprep_dir, subject_out_dir)

            confounds_wf = _setup_confounds_wf(postprocessing_config, pipeline_name, tr, confounds_export_path,
                subject_working_dir, log_dir, logger, mixing_file=mixing_file, noise_file=noise_file)
            
        except ValueError as ve:
            logger.warn(ve)
            logger.warn("Skipping confounds processing")

    if not confounds_only:
        image_export_path = _build_export_path(image_path, query_params["subject"], fmriprep_dir, subject_out_dir)

        image_wf = _setup_image_workflow(postprocessing_config, pipeline_name,
            tr, image_export_path, subject_working_dir, log_dir, logger, mask_image=mask_image,
            confounds=confounds_export_path, mixing_file=mixing_file, noise_file=noise_file)

    confound_regression = "ConfoundRegression" in postprocessing_config["ProcessingSteps"]

    postproc_wf = build_postprocessing_workflow(image_wf=image_wf, confounds_wf=confounds_wf, name=f"{pipeline_name}_Postprocessing_Pipeline",
        confound_regression=confound_regression, base_dir=subject_working_dir, crashdump_dir=log_dir)
    
    if postprocessing_config["WriteProcessGraph"]:
        _draw_graph(postproc_wf, "processing_graph", stream_dir, logger=logger)

    postproc_wf.inputs.inputnode.in_file = image_path
    postproc_wf.inputs.inputnode.confounds_file = confounds_path

    postproc_wf.run()

    # Disabled until this plotting works with .nii.gz
    # if not confounds_only:
    #     _plot_image_sample(image_export_path, title=pipeline_name)

    
def _get_mixing_file(bids, query_params, logger):
    logger.info("Searching for MELODIC mixing file")
    try:
        mixing_file = bids.get(
            **query_params, suffix="mixing", extension=".tsv", return_type="filename",
                desc="MELODIC", scope="derivatives"
        )[0]
        logger.info(f"MELODIC mixing file found: {mixing_file}")

        return mixing_file
    except IndexError:
        raise MixingFileNotFoundError(f"MELODIC mixing file for query {query_params} not found.")


def _get_noise_file(bids, query_params, logger):
    logger.info("Searching for AROMA noise ICs file")
    try:
        noise_file = bids.get(
            **query_params, suffix="AROMAnoiseICs", extension=".csv", return_type="filename",
                scope="derivatives"
        )[0]
        logger.info(f"AROMA noise ICs file found: {noise_file}")

        return noise_file
    except IndexError:
        raise NoiseFileNotFoundError(f"AROMA noise ICs file for query {query_params} not found.")


def _get_mask(bids, query_params, logger):
    # Find the subject's mask file
    logger.info("Searching for mask file")
    try:
        mask_image = bids.get(
            **query_params, suffix="mask", extension=".nii.gz", datatype="func", return_type="filename",
                desc="brain", scope="derivatives"
        )[0]
        logger.info(f"Mask file found: {mask_image}")

        return mask_image
    except IndexError:
        logger.warn(f"Mask image for search query: {query_params} not found")
        return None

def _get_tr(bids, query_params, logger):
    # To get the TR, we do another, similar query to get the sidecar and open it as a dict, because indexing metadata in
    # pybids is too slow to be worth just having the TR available
    # This can probably be done in just one query combined with the above

    image_to_process_json = bids.get(
        **query_params, extension=".json", datatype="func", 
        suffix="bold", desc="preproc", scope="derivatives", return_type="filename")[0]

    logger.info(f"Looking up TR in file: {image_to_process_json}")

    with open(image_to_process_json) as sidecar_file:
        sidecar_data = json.load(sidecar_file)
        tr = sidecar_data["RepetitionTime"]

        logger.info(f"Found TR: {tr}")

        return tr

def _get_confounds(bids, query_params, logger):
    # Find the subject's confounds file
    
    logger.info("Searching for confounds file")
    try:
        confounds = bids.get(
            **query_params, return_type="filename", extension=".tsv",
                desc="confounds", scope="derivatives"
        )[0]
        logger.info(f"Confound file found: {confounds}")

        return confounds
    except IndexError:
        logger.warn(f"Confound file for query {query_params} not found.")


def _setup_image_workflow(postprocessing_config, pipeline_name,
    tr, export_path, working_dir, log_dir, logger, mask_image=None, confounds=None,
    mixing_file=None, noise_file=None):

    logger.info(f"Building postprocessing workflow for: {pipeline_name}")
    wf = build_image_postprocessing_workflow(postprocessing_config, export_path=export_path,
        name=f"Image_Postprocessing_Pipeline",
        mask_file=mask_image, confounds_file = confounds,
        mixing_file=mixing_file, noise_file=noise_file,
        tr=tr,
        base_dir=working_dir, crashdump_dir=log_dir)

    return wf


def _build_export_path(image_path: os.PathLike, subject_id: str, fmriprep_dir: os.PathLike, subject_out_dir: os.PathLike):
    """Builds a new name for a processed image.

    Args:
        image_path (os.PathLike): The path to the original image file.
        subject_out_dir (os.PathLike): The destination directory.

    Returns:
        os.PathLike: Save path for an image file.
    """
    # Copy the directory structure following the subject-id from the fmriprep dir
    out_path = Path(image_path).relative_to(Path(fmriprep_dir) / ("sub-" + subject_id))
    export_path = Path(subject_out_dir) / str(out_path)
    export_folder = export_path.parent

    # Create the output folder if it doesn't exist
    if not export_folder.exists():
        export_folder.mkdir(parents=True)

    export_path = Path(subject_out_dir) / str(out_path).replace("preproc", "postproc")

    print(f"Export path: {export_path}")

    return export_path


def _setup_confounds_wf(postprocessing_config, pipeline_name, tr, export_file, 
    working_dir, log_dir, logger, mixing_file=None, noise_file=None):

    # TODO: Run this async or batch
    logger.info(f"Building confounds workflow for {pipeline_name}")
    
    logger.info(f"Postprocessed confound out file: {export_file}")

    confounds_wf = build_confounds_processing_workflow(postprocessing_config,
        export_file=export_file, tr=tr,
        name=f"Confounds_Processing_Pipeline",
        mixing_file=mixing_file, noise_file=noise_file,
        base_dir=working_dir, crashdump_dir=log_dir)

    return confounds_wf


def _draw_graph(wf: pe.Workflow, graph_name: str, out_dir: Path, graph_style: str="colored", logger: logging.Logger=None):
    graph_image_path = out_dir / f"{graph_name}.dot"
    if logger:
        logger.info(f"Drawing confounds workflow graph: {graph_image_path}")
    
        wf.write_graph(dotfilename = graph_image_path, graph2use=graph_style)
    
    # Delete the unessecary dot file
    # Due to parallel compute, an exists check guards the unlink incase it is deleted early by another process
    if graph_image_path.exists():
        graph_image_path.unlink()
    


# def _plot_image_sample(image_path: os.PathLike, title: str= "image_sample.png", display_mode: str="mosaic"):
#     """Plots a sample volume from the midpoint of the given 4D image to allow quick
#     visual inspection of the fidelity of processing results.

#     Args:
#         image_path (os.PathLike): Path to the 4D image to plot.
#         title (str, optional): The title for the plot. Defaults to "image_sample.png".
#         display_mode (str, optional): Method for displaying the plot. Defaults to "mosaic".
#     """

#     main_image = load_img(image_path)

#     # Grab a slice from the midpoint
#     image_slice = index_img(main_image, int(main_image.shape[IMAGE_TIME_DIMENSION_INDEX] / 2))

#     # Create a save path in the same directory as the image_path
#     output_path = Path(image_path).parent / title

#     plotting.plot_epi(image_slice, title=title, output_file=output_path, display_mode=display_mode)


def _fetch_postprocessing_stream_config(config: dict, output_dir: os.PathLike, processing_stream:str=DEFAULT_PROCESSING_STREAM_NAME):
    """
    The postprocessing stream config is a subset of the main configuration's postprocessing config, based on
    selections made in the processing streams config.

    This stream postprocessing config is saved as a seperate configuration file at the level of the output folder / stream folder and
    is referred to by the workflow builders.
    """
    stream_output_dir = Path(output_dir) / processing_stream
    if not stream_output_dir.exists():
        stream_output_dir.mkdir()

    postprocessing_description_file = Path(stream_output_dir) / PROCESSING_DESCRIPTION_FILE_NAME
    postprocessing_config = _postprocessing_config_apply_processing_stream(config, processing_stream=processing_stream)
    _write_processing_description_file(postprocessing_config, postprocessing_description_file)

    return postprocessing_config


def _write_processing_description_file(postprocessing_config: dict, processing_description_file: os.PathLike):
    processing_steps = postprocessing_config["ProcessingSteps"]
    processing_step_options = postprocessing_config["ProcessingStepOptions"]
    processing_step_options_reference = processing_step_options.copy()
    confound_options = postprocessing_config["ConfoundOptions"]

    # Remove processing options not used
    for step_option in processing_step_options_reference.keys():
        if step_option not in processing_steps:
            processing_step_options.pop(step_option)

    # Write the processing file
    with open(processing_description_file, 'w') as file_to_write:
        json.dump(postprocessing_config, file_to_write, indent=4)


def _postprocessing_config_apply_processing_stream(config: dict, processing_stream:str=DEFAULT_PROCESSING_STREAM_NAME):
    postprocessing_config = _get_postprocessing_config(config)
    processing_streams = _get_processing_streams(config)
    
    # If using the default stream, no need to update postprocessing config
    if processing_stream == DEFAULT_PROCESSING_STREAM_NAME:
        return

    # Iterate through the available processing streams and see if one matches the one requested
    # The default processing stream name won't be in this list - it refers to the base PostProcessingOptions
    for stream in processing_streams:
        stream_options = stream["PostProcessingOptions"]

        if stream["ProcessingStream"] == processing_stream:
            # Use deep update to impart the processing stream options into the postprocessing config
            postprocessing_config = pydantic.utils.deep_update(postprocessing_config, stream_options)
            return postprocessing_config

    raise ValueError(f"No stream found in configuration with name: {processing_stream}")


def _get_postprocessing_config(config: dict):
    return config["PostProcessingOptions2"]


def _get_processing_streams(config: dict):
    return config["ProcessingStreams"]


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


def _get_images_to_process(subject_id, image_space, bids, logger, tasks=None, acquisitions=None):
    logger.info(f"Searching for images to process")
    logger.info(f"Target image space: {image_space}")
    
    # Find the subject's preproc images
    try:
        images_to_process = []

        search_args = {"subject": subject_id, "extension": "nii.gz", "datatype": "func", 
                "suffix": "bold", "desc": "preproc", "scope": "derivatives", "space": image_space}
        if tasks:
            search_args["task"] = tasks
            logger.info(f"Targeting task(s): {tasks}")
        else:
            logger.info(f"Targeting all available tasks.")

        if acquisitions:
            search_args["acquisition"] = acquisitions
            logger.info(f"Targeting acquisition(s): {acquisitions}")
        else:
            logger.info(f"Targeting all available acquisitions.")
        
        images_to_process = bids.get(**search_args)

        if len(images_to_process) == 0:
            raise NoImagesFoundError(f"No preproc BOLD images found for sub-{subject_id} in space {image_space}, task(s): {str(tasks)}.")

        logger.info(f"Found images: {len(images_to_process)}")
        return images_to_process
    except IndexError:
        raise NoImagesFoundError(f"No preproc BOLD image for subject {subject_id} found.")


def _create_image_submission_strings(images_to_process, bids_dir, fmriprep_dir, pybids_db_path, out_dir, subject_out_dir, processing_stream,
    subject_working_dir, config_file, log_dir, logger):
    
        logger.info(f"Building image job submission strings")

        submission_strings = {}
        SUBMISSION_STRING_TEMPLATE = ("postprocess_image {config_file} "
            "{image_path} {bids_dir} {fmriprep_dir} {pybids_db_path} {out_dir} {subject_out_dir} {processing_stream} {subject_working_dir} {log_dir}")
        
        logger.info("Creating submission strings")
        for image in images_to_process:
            key = f"Postprocessing_{str(Path(image.path).stem)}"
            
            submission_strings[key] = SUBMISSION_STRING_TEMPLATE.format(config_file=config_file,
                                                            image_path=image.path,
                                                            bids_dir=bids_dir,
                                                            fmriprep_dir=fmriprep_dir,
                                                            pybids_db_path=pybids_db_path,
                                                            out_dir=out_dir,
                                                            subject_out_dir=subject_out_dir,
                                                            processing_stream=processing_stream,
                                                            subject_working_dir=subject_working_dir,
                                                            log_dir=log_dir)
        return submission_strings


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


def _create_submission_strings(subjects_to_process, bids_dir, fmriprep_dir, config_file, pybids_db_path, output_dir, 
    processing_stream, log_dir, logger, batch_manager, submit):
    
    logger.info("Creating submission strings")
    submission_strings = {}

    batch_flag = ""
    submit_flag = ""
    if not batch_manager:
        batch_flag = "-no-batch"
    if submit:
        submit_flag = "-submit"

    SUBMISSION_STRING_TEMPLATE = """postprocess_subject {subject_id} {bids_dir} {fmriprep_dir} {output_dir} {processing_stream} {config_file} {index_dir} {log_dir} {batch} {submit}"""
    for subject in subjects_to_process:
        key = "Postprocessing_sub-" + subject
        submission_strings[key] = SUBMISSION_STRING_TEMPLATE.format(subject_id=subject,
                                                        bids_dir=bids_dir,
                                                        fmriprep_dir=fmriprep_dir,
                                                        config_file=config_file,
                                                        index_dir=pybids_db_path,
                                                        output_dir=output_dir,
                                                        processing_stream=processing_stream,
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


def _add_file_handler(logger: logging.Logger, log_dir: Path, f_name: str):
    if not log_dir.exists():
        log_dir.mkdir(parents=True)

    # Create log handler
    f_handler = logging.FileHandler(log_dir / f_name)
    f_handler.setLevel(logging.DEBUG)
    
    # Create log format
    f_format = logging.Formatter('%(asctime)s - %(levelname)s: %(name)s - %(message)s')
    f_handler.setFormatter(f_format)

    # Add handler to the logger
    logger.addHandler(f_handler)


def _get_subject_working_dir(working_dir, out_dir, subject_id, processing_stream, logger):
     # If no top-level working directory is provided, make one in the out_dir
    if not working_dir:
        subject_working_dir = out_dir / "working" / processing_stream / ("sub-" + subject_id)
    # Otherwise, use the provided top-level directory as a base, and name working directory after the subject
    else:
        subject_working_dir = Path(working_dir) / processing_stream / ("sub-" + subject_id)

    # Create the working directory, if it doesn't exist
    if not subject_working_dir.exists():
        logger.info(f"Creating subject working directory: {subject_working_dir}")
        subject_working_dir.mkdir(exist_ok=True, parents=True)

    return subject_working_dir
