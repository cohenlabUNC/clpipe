import os
import sys
from pathlib import Path

from .batch_manager import BatchManager, Job
from .config.options import ProjectOptions
from .utils import get_logger
from .status import needs_processing, write_record

STEP_NAME = "fmriprep-process"
BASE_SINGULARITY_CMD = (
    "unset PYTHONPATH; {templateflow1} singularity run -B {templateflow2}"
    "{bindPaths} {batchcommands} {fmriprepInstance} {bids_dir} {output_dir} "
    "participant --participant-label {participantLabels} -w {working_dir} "
    "--fs-license-file {fslicense} {threads} {useAROMA} {other_opts}"
)
BASE_DOCKER_CMD = (
    "docker run --rm -ti "
    "-v {fslicense}:/opt/freesurfer/license.txt:ro "
    "-v {bids_dir}:/data:ro -v {output_dir}:/out "
    "-v {working_dir}:/work "
    "{docker_fmriprep} /data /out participant -w /work {threads} {useAROMA} "
    "{other_opts} --participant-label {participantLabels}"
)
TEMPLATE_1 = "export SINGULARITYENV_TEMPLATEFLOW_HOME={templateflowpath};"
TEMPLATE_2 = \
    "${{TEMPLATEFLOW_HOME:-$HOME/.cache/templateflow}}:{templateflowpath},"
USE_AROMA_FLAG = "--use-aroma"
N_THREADS_FLAG = "--nthreads"
TEMPLATE_FLOW_CACHE_PATH = ".cache/templateflow"


def fmriprep_process(bids_dir=None, working_dir=None, output_dir=None, 
                           config_file=None, subjects=None, log_dir=None,
                           status_cache=None, submit=False, debug=False):
    """
    This command runs a BIDS formatted dataset through fMRIprep. 
    Specify subject IDs to run specific subjects. If left blank,
    runs all subjects.
    """
    # os.makedirs(config.fmriprep.working_directory, exist_ok=True)
    config: ProjectOptions = ProjectOptions.load(config_file)
    config.fmriprep.load_cli_args(
        output_directory = output_dir,
        working_directory = working_dir,
        bids_directory = bids_dir,
        log_directory = log_dir
    )
    setup_dirs(config)

    logger = get_logger(STEP_NAME, debug=debug, log_dir=config.get_logs_dir())

    # Check to make sure working directory has been changed from the default
    if config.fmriprep.working_directory == ProjectOptions().fmriprep.working_directory:
        logger.error("A working directory for this step must be provided in your config file.")
        sys.exit(1)

    if not any([
        config.fmriprep.bids_directory, 
        config.fmriprep.output_directory,
        config.fmriprep.working_directory,
        config.fmriprep.log_directory
    ]):
        logger.error(
            'Please make sure the BIDS, working and output directories are '
            'specified in either the configfile or in the command. '
            'At least one is not specified.'
        )
        sys.exit(1)

    logger.info(f"Starting fMRIprep job targeting: {config.fmriprep.bids_directory}")
    logger.debug(f"Using config file: {config_file}")

    template_1 = ""
    template_2 = ""
    if config.fmriprep.templateflow_toggle:
        logger.debug("Template Flow toggle: ON")

        if config.fmriprep.templateflow_path == "":
            logger.error("Template flow toggle on but no template flow path given.")
            sys.exit(1)
        logger.debug(f"Template Flow path: {config.fmriprep.templateflow_path}")

        # Templateflow requires a caching directory that it for some reason
        #   does not make itself, so it is created here.
        user_templateflow_path = Path.home() / TEMPLATE_FLOW_CACHE_PATH
        if not user_templateflow_path.exists():
            user_templateflow_path.mkdir(parents=True)

        template_1 = TEMPLATE_1.format(
            templateflowpath = config.fmriprep.templateflow_path
        )
        template_2 = TEMPLATE_2.format(
            templateflowpath = config.fmriprep.templateflow_path
        )
        
    if config.fmriprep.docker_toggle:
        logger.debug("Using container type: Docker")
        logger.debug(f"Docker fMRIprep version: {config.fmriprep.fmriprep_path}")
    else:
        logger.debug("Using container type: Singularity")
        logger.debug(f"Container path: {config.fmriprep.docker_fmriprep_version}")


    use_aroma_arg = ""
    if USE_AROMA_FLAG in config.fmriprep.commandline_opts:
        logger.debug("Use AROMA: ON")  
    elif config.fmriprep.use_aroma:
        logger.debug("Use AROMA: ON")
        use_aroma_arg = USE_AROMA_FLAG
    else:
        logger.debug("Use AROMA: OFF")

    if not subjects:
        sublist = [o.replace('sub-', '') for o in os.listdir(config.fmriprep.bids_directory)
                   if os.path.isdir(os.path.join(config.fmriprep.bids_directory, o)) and 'sub-' in o]
    else:
        sublist = subjects

    if status_cache:
        logger.info(f"Using status log: {status_cache}")
        sublist = needs_processing(sublist, status_cache, step=STEP_NAME)
        if len(sublist) == 0:
            logger.info((
                "No subjects need processing. If this seems incorrect, "
                f"you may need to clear 'submitted' {STEP_NAME} entries from "
                "your status log."
            ))
            sys.exit(0)

    logger.info(f"Targeting subject(s): {', '.join(sublist)}")

    batch_manager = BatchManager(config.batch_config_path, config.fmriprep.log_directory, debug=debug)
    batch_manager.update_mem_usage(config.fmriprep.fmriprep_memory_usage)
    batch_manager.update_time(config.fmriprep.fmriprep_time_usage)
    batch_manager.update_nthreads(config.fmriprep.n_threads)
    batch_manager.update_email(config.email_address)

    thread_command_active = batch_manager.config['ThreadCommandActive']
    batch_commands = batch_manager.config["FMRIPrepBatchCommands"]
    singularity_bind_paths = batch_manager.config['SingularityBindPaths']

    threads_arg = ''
    if thread_command_active:
        logger.debug("Threads command: ACTIVE")
        threads_arg = f'{N_THREADS_FLAG} ' + batch_manager.get_threads_command()[1]
        
    fmriprep_args = {
        "bids_dir": config.fmriprep.bids_directory,
        "output_dir": config.fmriprep.output_directory,
        "working_dir": config.fmriprep.working_directory,
        "fslicense": config.fmriprep.freesurfer_license_path,
        "threads": threads_arg,
        "useAROMA": use_aroma_arg,
        "other_opts": config.fmriprep.commandline_opts
    }

    for sub in sublist:
        fmriprep_args["participantLabels"] = sub
        if config.fmriprep.docker_toggle:
            fmriprep_args["docker_fmriprep"] = config.fmriprep.docker_fmriprep_version

            submission_string = BASE_DOCKER_CMD.format(**fmriprep_args)    
        else:
            fmriprep_args["templateflow1"] = template_1
            fmriprep_args["templateflow2"] = template_2
            fmriprep_args["fmriprepInstance"] = config.fmriprep.fmriprep_path
            fmriprep_args["batchcommands"] = batch_commands
            fmriprep_args["bindPaths"] = singularity_bind_paths

            submission_string = BASE_SINGULARITY_CMD.format(**fmriprep_args)
        batch_manager.addjob(
            Job("sub-" + sub + "_fmriprep", submission_string)
        )

    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
        if status_cache:
            for sub in sublist:
                write_record(sub, cache_path=status_cache, step=STEP_NAME)
    else:
        batch_manager.print_jobs()
    sys.exit(0)


def setup_dirs(config: ProjectOptions):
    os.makedirs(config.fmriprep.output_directory, exist_ok=True)
    os.makedirs(config.fmriprep.log_directory, exist_ok=True)
