import os
import sys
import click

from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
from .utils import get_logger, add_file_handler
from .status import needs_processing, write_record
from .config import LOG_DIR_HELP, SUBMIT_HELP, DEBUG_HELP, STATUS_CACHE_HELP, \
    CLICK_DIR_TYPE, CLICK_DIR_TYPE_EXISTS, CLICK_FILE_TYPE_EXISTS, \
    CLICK_FILE_TYPE

COMMAND_NAME = "preprocess"
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

CONFIG_HELP = (
    "Use a given configuration file. If left blank, uses the default config "
    "file, requiring definition of BIDS, working and output directories."
)
BIDS_DIR_HELP = (
    "Which BIDS directory to process. If a configuration file is provided "
    "with a BIDS directory, this argument is not necessary."
)
WORKING_DIR_HELP = (
    "Where to generate the working directory. If a configuration file is "
    "provided with a working directory, this argument is not necessary."
)
OUTPUT_DIR_HELP = (
    "Where to put the preprocessed data. If a configuration file is provided "
    "with a output directory, this argument is not necessary."
)

@click.command(COMMAND_NAME)
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', default=None, type=CLICK_FILE_TYPE_EXISTS, 
              help=CONFIG_HELP)
@click.option('-bids_dir', type=CLICK_DIR_TYPE_EXISTS,
              help=BIDS_DIR_HELP)
@click.option('-working_dir', type=CLICK_DIR_TYPE, 
              help=WORKING_DIR_HELP)
@click.option('-output_dir', type=CLICK_DIR_TYPE,
              help=OUTPUT_DIR_HELP)
@click.option('-log_dir', type=CLICK_DIR_TYPE, help=LOG_DIR_HELP)
@click.option('-submit', is_flag=True, default=False, help=SUBMIT_HELP)
@click.option('-debug', is_flag=True, help=DEBUG_HELP)
@click.option('-status_cache', default=None, type=CLICK_FILE_TYPE, 
              help=STATUS_CACHE_HELP)
def fmriprep_process_cli(bids_dir, working_dir, output_dir, config_file, 
                         subjects, log_dir, submit, debug, status_cache):
    """Submit BIDS-formatted images to fMRIPrep"""

    fmriprep_process(
        bids_dir=bids_dir, working_dir=working_dir,
        output_dir=output_dir, config_file=config_file, 
        subjects=subjects, log_dir=log_dir, submit=submit, debug=debug, 
        status_cache=status_cache)


def fmriprep_process(bids_dir=None, working_dir=None, output_dir=None, 
                           config_file=None, subjects=None, log_dir=None,
                           status_cache=None, submit=False, debug=False):
    """
    This command runs a BIDS formatted dataset through fMRIprep. 
    Specify subject IDs to run specific subjects. If left blank,
    runs all subjects.
    """

    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.setup_fmriprep_directories(
        bids_dir, working_dir, output_dir, log_dir
    )

    config = config.config
    project_dir = config["ProjectDirectory"]
    bids_dir = config['FMRIPrepOptions']['BIDSDirectory']
    working_dir = config['FMRIPrepOptions']['WorkingDirectory']
    output_dir = config['FMRIPrepOptions']['OutputDirectory']
    log_dir = config['FMRIPrepOptions']['LogDirectory']
    template_flow_path = config["FMRIPrepOptions"]["TemplateFlowPath"]
    batch_config = config['BatchConfig']
    mem_usage = config['FMRIPrepOptions']['FMRIPrepMemoryUsage']
    time_usage = config['FMRIPrepOptions']['FMRIPrepTimeUsage']
    n_threads = config['FMRIPrepOptions']['NThreads']
    email = config["EmailAddress"]
    cmd_line_opts = config['FMRIPrepOptions']['CommandLineOpts']
    use_aroma_flag = config['FMRIPrepOptions']['UseAROMA']
    docker_toggle = config['FMRIPrepOptions']['DockerToggle']
    docker_fmriprep_version = \
        config['FMRIPrepOptions']['DockerFMRIPrepVersion']
    freesurfer_license_path = \
        config['FMRIPrepOptions']['FreesurferLicensePath']
    fmriprep_path = config['FMRIPrepOptions']['FMRIPrepPath']

    add_file_handler(os.path.join(project_dir, "logs"))
    logger = get_logger(STEP_NAME, debug=debug)

    if not any([bids_dir, output_dir, working_dir, log_dir]):
        logger.error(
            'Please make sure the BIDS, working and output directories are '
            'specified in either the configfile or in the command. '
            'At least one is not specified.'
        )
        sys.exit(1)

    logger.info(f"Starting fMRIprep job targeting: {bids_dir}")
    logger.debug(f"Using config file: {config_file}")

    template_1 = ""
    template_2 = ""
    if config['FMRIPrepOptions']['TemplateFlowToggle']:
        logger.debug("Template Flow toggle: ON")
        logger.debug(f"Template Flow path: {template_flow_path}")
        template_1 = TEMPLATE_1.format(
            templateflowpath = template_flow_path
        )
        template_2 = TEMPLATE_2.format(
            templateflowpath = template_flow_path
        )
        
    if docker_toggle:
        logger.debug("Using container type: Docker")
        logger.debug(f"Docker fMRIprep version: {docker_fmriprep_version}")
    else:
        logger.debug("Using container type: Singularity")
        logger.debug(f"Container path: {fmriprep_path}")

    other_opts = cmd_line_opts
    
    use_aroma = ""
    if USE_AROMA_FLAG in other_opts:
        logger.debug("Use AROMA: ON")  
    elif use_aroma_flag:
        logger.debug("Use AROMA: ON")
        use_aroma = USE_AROMA_FLAG

    if not subjects:
        sublist = [o.replace('sub-', '') for o in os.listdir(bids_dir)
                   if os.path.isdir(os.path.join(bids_dir, o)) and 'sub-' in o]
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

    batch_manager = BatchManager(batch_config, log_dir, debug=debug)
    batch_manager.update_mem_usage(mem_usage)
    batch_manager.update_time(time_usage)
    batch_manager.update_nthreads(n_threads)
    batch_manager.update_email(email)

    thread_command_active = batch_manager.config['ThreadCommandActive']
    batch_commands = batch_manager.config["FMRIPrepBatchCommands"]
    singularity_bind_paths = batch_manager.config['SingularityBindPaths']

    threads = ''
    if thread_command_active:
        logger.debug("Threads command: ACTIVE")
        threads = f'{N_THREADS_FLAG} ' + batch_manager.get_threads_command()[1]
        
    fmriprep_args = {
        "bids_dir": bids_dir,
        "output_dir": output_dir,
        "working_dir": working_dir,
        "fslicense": freesurfer_license_path,
        "threads": threads,
        "useAROMA": use_aroma,
        "other_opts": other_opts
    }

    for sub in sublist:
        fmriprep_args["participantLabels"] = sub
        if docker_toggle:
            fmriprep_args["docker_fmriprep"] = docker_fmriprep_version

            submission_string = BASE_DOCKER_CMD.format(**fmriprep_args)    
        else:
            fmriprep_args["templateflow1"] = template_1
            fmriprep_args["templateflow2"] = template_2
            fmriprep_args["fmriprepInstance"] = fmriprep_path
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
