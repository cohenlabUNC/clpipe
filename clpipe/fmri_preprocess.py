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
TEMPLATE_2 = "${{TEMPLATEFLOW_HOME:-$HOME/.cache/templateflow}}:{templateflowpath},"
USE_AROMA_FLAG = "--use-aroma"
N_THREADS_FLAG = "--nthreads"


def fmriprep_process(bids_dir=None, working_dir=None, output_dir=None, 
                     config_file=None, subjects=None,log_dir=None,submit=False, 
                     debug=False):
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
    if not any([config.config['FMRIPrepOptions']['BIDSDirectory'], 
                config.config['FMRIPrepOptions']['OutputDirectory'],
                config.config['FMRIPrepOptions']['WorkingDirectory'],
                config.config['FMRIPrepOptions']['LogDirectory']]):
        raise ValueError(
            'Please make sure the BIDS, working and output directories are '
            'specified in either the configfile or in the command. '
            'At least one is not specified.'
        )

    template1 = ""
    template2 = ""

    if config.config['FMRIPrepOptions']['TemplateFlowToggle']:
        template1 = TEMPLATE_1.format(
            templateflowpath = config.config["FMRIPrepOptions"]["TemplateFlowPath"]
        )
        template2 = TEMPLATE_2.format(
            templateflowpath = config.config["FMRIPrepOptions"]["TemplateFlowPath"]
        )
        
    otherOpts = config.config['FMRIPrepOptions']['CommandLineOpts']
    useAROMA = ""
    if config.config['FMRIPrepOptions']['UseAROMA']:
        # Check to make sure '--use-aroma' isn't already specified in otherOpts, to prevent duplicating the option
        if USE_AROMA_FLAG not in otherOpts:
            useAROMA = USE_AROMA_FLAG

    if not subjects:
        subjectstring = "ALL"
        sublist = [o.replace('sub-', '') for o in os.listdir(config.config['FMRIPrepOptions']['BIDSDirectory'])
                   if os.path.isdir(os.path.join(config.config['FMRIPrepOptions']['BIDSDirectory'], o)) and 'sub-' in o]
    else:
        subjectstring = " , ".join(subjects)
        sublist = subjects

    batch_manager = BatchManager(config.config['BatchConfig'], config.config['FMRIPrepOptions']['LogDirectory'])
    batch_manager.update_mem_usage(config.config['FMRIPrepOptions']['FMRIPrepMemoryUsage'])
    batch_manager.update_time(config.config['FMRIPrepOptions']['FMRIPrepTimeUsage'])
    batch_manager.update_nthreads(config.config['FMRIPrepOptions']['NThreads'])
    batch_manager.update_email(config.config["EmailAddress"])

    threads = ''
    if batch_manager.config['ThreadCommandActive']:
        threads = f'{N_THREADS_FLAG} ' + batch_manager.get_threads_command()[1]
        
    for sub in sublist:
        if config.config['FMRIPrepOptions']['DockerToggle']:     
            submission_string = BASE_DOCKER_CMD.format(
                docker_fmriprep=config.config['FMRIPrepOptions']['DockerFMRIPrepVersion'],
                bids_dir=config.config['FMRIPrepOptions']['BIDSDirectory'],
                output_dir=config.config['FMRIPrepOptions']['OutputDirectory'],
                working_dir=config.config['FMRIPrepOptions']['WorkingDirectory'],
                participantLabels=sub,
                fslicense=config.config['FMRIPrepOptions']['FreesurferLicensePath'],
                threads= threads,
                useAROMA=useAROMA,
                otheropts=otherOpts
            )
        else:
            submission_string = BASE_SINGULARITY_CMD.format(
                templateflow1 = template1,
                templateflow2 = template2,
                fmriprepInstance=config.config['FMRIPrepOptions']['FMRIPrepPath'],
                bids_dir=config.config['FMRIPrepOptions']['BIDSDirectory'],
                output_dir=config.config['FMRIPrepOptions']['OutputDirectory'],
                working_dir=config.config['FMRIPrepOptions']['WorkingDirectory'],
                batchcommands=batch_manager.config["FMRIPrepBatchCommands"],
                participantLabels=sub,
                fslicense=config.config['FMRIPrepOptions']['FreesurferLicensePath'],
                threads= threads,
                useAROMA=useAROMA,
                bindPaths=batch_manager.config['SingularityBindPaths'],
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
