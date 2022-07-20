import os
import sys
import logging
from .batch_manager import BatchManager, Job
from .config_json_parser import ClpipeConfigParser
from .error_handler import exception_handler

BASE_SINGULARITY_CMD = (
    "unset PYTHONPATH; {templateflow1} singularity run -B {templateflow2}"
    "{bindPaths} {batchcommands} {fmriprepInstance} {bids_dir} {output_dir} "
    "participant --participant-label {participantLabels} -w {working_dir} "
    "--fs-license-file {fslicense} {threads} {useAROMA} {otheropts}"
)

BASE_DOCKER_CMD = (
    "docker run --rm -ti "
    "-v {fslicense}:/opt/freesurfer/license.txt:ro "
    "-v {bids_dir}:/data:ro -v {output_dir}:/out "
    "-v {working_dir}:/work "
    "{docker_fmriprep} /data /out participant -w /work {threads} {useAROMA} "
    "{otheropts} --participant-label {participantLabels}"
)

TEMPLATE_1 = "export SINGULARITYENV_TEMPLATEFLOW_HOME={templateflowpath};"
TEMPLATE_2 = \
    "${{TEMPLATEFLOW_HOME:-$HOME/.cache/templateflow}}:{templateflowpath},"
USE_AROMA_FLAG = "--use-aroma"
N_THREADS_FLAG = "--nthreads"


def fmriprep_process(bids_dir=None, working_dir=None, output_dir=None, 
                     config_file=None, subjects=None, log_dir=None,
                     submit=False, debug=False):
    """
    This command runs a BIDS formatted dataset through fMRIprep. 
    Specify subject IDs to run specific subjects. If left blank,
    runs all subjects.
    """

    if not debug:
        sys.excepthook = exception_handler
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    config = ClpipeConfigParser()
    config.config_updater(config_file)
    config.setup_fmriprep_directories(
        bids_dir, working_dir, output_dir, log_dir
    )

    config = config.config
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
    thread_command_active = batch_manager.config['ThreadCommandActive']
    cmd_line_opts = config['FMRIPrepOptions']['CommandLineOpts']
    use_aroma = config['FMRIPrepOptions']['UseAROMA']
    docker_toggle = config['FMRIPrepOptions']['DockerToggle']
    docker_fmriprep_version = \
        config['FMRIPrepOptions']['DockerFMRIPrepVersion']
    freesurfer_license_path = \
        config['FMRIPrepOptions']['FreesurferLicensePath']
    batch_commands = batch_manager.config["FMRIPrepBatchCommands"]
    singularity_bind_paths = batch_manager.config['SingularityBindPaths']
    fmriprep_path = config['FMRIPrepOptions']['FMRIPrepPath']

    if not any([bids_dir, output_dir, working_dir, log_dir]):
        raise ValueError(
            'Please make sure the BIDS, working and output directories are '
            'specified in either the configfile or in the command. '
            'At least one is not specified.'
        )

    template1 = ""
    template2 = ""
    if config['FMRIPrepOptions']['TemplateFlowToggle']:
        template1 = TEMPLATE_1.format(
            templateflowpath = template_flow_path
        )
        template2 = TEMPLATE_2.format(
            templateflowpath = template_flow_path
        )
        
    otherOpts = cmd_line_opts
    useAROMA = ""
    if use_aroma:
        # Check to make sure '--use-aroma' isn't already specified in 
        # otherOpts, to prevent duplicating the option
        if USE_AROMA_FLAG not in otherOpts:
            useAROMA = USE_AROMA_FLAG

    if not subjects:
        sublist = [o.replace('sub-', '') for o in os.listdir(bids_dir)
                   if os.path.isdir(os.path.join(bids_dir, o)) and 'sub-' in o]
    else:
        sublist = subjects

    batch_manager = BatchManager(batch_config, log_dir)
    batch_manager.update_mem_usage(mem_usage)
    batch_manager.update_time(time_usage)
    batch_manager.update_nthreads(n_threads)
    batch_manager.update_email(email)

    threads = ''
    if thread_command_active:
        threads = f'{N_THREADS_FLAG} ' + batch_manager.get_threads_command()[1]
        
    for sub in sublist:
        if docker_toggle:     
            submission_string = BASE_DOCKER_CMD.format(
                docker_fmriprep=docker_fmriprep_version,
                bids_dir=bids_dir,
                output_dir=output_dir,
                working_dir=working_dir,
                participantLabels=sub,
                fslicense=freesurfer_license_path,
                threads= threads,
                useAROMA=useAROMA,
                otheropts=otherOpts
            )
        else:
            submission_string = BASE_SINGULARITY_CMD.format(
                templateflow1 = template1,
                templateflow2 = template2,
                fmriprepInstance=fmriprep_path,
                bids_dir=bids_dir,
                output_dir=output_dir,
                working_dir=working_dir,
                batchcommands=batch_commands,
                participantLabels=sub,
                fslicense=freesurfer_license_path,
                threads= threads,
                useAROMA=useAROMA,
                bindPaths=singularity_bind_paths,
                otheropts=otherOpts
            )
        batch_manager.addjob(
            Job("sub-" + sub + "_fmriprep", submission_string)
        )

    batch_manager.compilejobstrings()
    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()
