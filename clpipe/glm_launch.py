import os
import sys
from pathlib import Path

from .config import *
from .config_json_parser import GLMConfigParser, ClpipeConfigParser
from .batch_manager import BatchManager, Job
from .utils import add_file_handler, get_logger

DEFAULT_L1_MEMORY_USAGE = "10G"
DEFAULT_L1_TIME_USAGE = "10:00:00"
DEFAULT_L1_N_THREADS = "4"

DEFAULT_L2_MEMORY_USAGE = "5G"
DEFAULT_L2_TIME_USAGE = "5:00:00"
DEFAULT_L2_N_THREADS = "4"

STEP_NAME = "glm-launch"

# Unset PYTHONPATH to ensure FSL uses its own internal python
#   libraries
SUBMISSION_STRING_TEMPLATE = ("unset PYTHONPATH; feat {fsf_file}")
DEPRECATION_MSG = "Using deprecated GLM setup file."


def glm_launch(glm_config_file: str=None, level: int=L1,
                          model: str=None, test_one: bool=False, 
                          submit: bool=False, debug: bool=False):
    glm_config_parser = GLMConfigParser(glm_config_file)
    glm_config = glm_config_parser.config

    warn_deprecated = False
    try:
        # These working indicates the user has a glm_config file from < v1.7.4
        # In this case, use the GLMSetupOptions block as root dict
        # TODO: when we get centralized config classes, this can be handled there
        parent_config = glm_config['GLMSetupOptions']['ParentClpipeConfig']
        warn_deprecated = True
    except KeyError:
        parent_config = glm_config["ParentClpipeConfig"]

    config = ClpipeConfigParser()
    config.config_updater(parent_config)

    project_dir = config.config["ProjectDirectory"]
    add_file_handler(os.path.join(project_dir, "logs"))
    logger = get_logger(STEP_NAME, debug=debug)

    if warn_deprecated:
        logger.warn(DEPRECATION_MSG)

    if level in VALID_L1:
        level = "L1"
        setup = 'Level1Setups'
    elif level in VALID_L2:
        level = "L2"
        setup = 'Level2Setups'
    else:
        logger.error(f"Level must be {L1} or {L2}")
        sys.exit(1)

    logger.info(f"Setting up {level} .fsf launch using model: {model}")

    block = [x for x in glm_config[setup] \
            if x['ModelName'] == str(model)]
    if len(block) is not 1:
        logger.error("Model not found, or multiple entries found.")
        sys.exit(1)
    model_options = block[0]

    try:
        batch_options = model_options["BatchOptions"]

        memory_usage = batch_options["MemoryUsage"]
        time_usage = batch_options["TimeUsage"]
        n_threads = int(batch_options["NThreads"])
        batch_config_path = batch_options["BatchConfig"]
        email = batch_options["Email"]
    except KeyError:
        if level == L1:
            memory_usage = DEFAULT_L1_MEMORY_USAGE
            time_usage = DEFAULT_L1_TIME_USAGE
            n_threads = DEFAULT_L1_N_THREADS
        elif level == L2:
            memory_usage = DEFAULT_L2_MEMORY_USAGE
            time_usage = DEFAULT_L2_TIME_USAGE
            n_threads = DEFAULT_L2_N_THREADS

        batch_config_path = DEFAULT_BATCH_CONFIG_PATH
        email = None

    fsf_dir = model_options["FSFDir"]
    logger.info(f"Targeting .fsfs in dir: {fsf_dir}")
    out_dir = model_options["OutputDir"]
    logger.info(f"Output dir: {out_dir}")

    try:
        log_dir = model_options["LogDir"]
        if log_dir == "":
            log_dir = out_dir
    except KeyError:
        log_dir = out_dir
    logger.info(f"Using log dir: {log_dir}")

    batch_manager = _setup_batch_manager(
        batch_config_path, log_dir,
        memory_usage=memory_usage, time_usage=time_usage, n_threads=n_threads,
        email=email)

    submission_strings = _create_submission_strings(
        fsf_dir, test_one=test_one)
   
    num_jobs = len(submission_strings)

    _populate_batch_manager(batch_manager, submission_strings)
    if submit:
        logger.info(f"Running {num_jobs} job(s) in batch mode")
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()
    sys.exit(0)


def _setup_batch_manager(batch_config_path: str, log_dir: str, 
                         memory_usage: str = None, time_usage: str = None, 
                         n_threads: int = None, email: str = None, ):
    batch_manager = BatchManager(batch_config_path, log_dir)
    if memory_usage:
        batch_manager.update_mem_usage(memory_usage)
    if time_usage:
        batch_manager.update_time(time_usage)
    if n_threads:
        batch_manager.update_nthreads(n_threads)
    if email:
        batch_manager.update_email(email)

    return batch_manager

 
def _create_submission_strings(fsf_files: os.PathLike, 
                               test_one:bool=False):

        submission_strings = {}
        
        for fsf in Path(fsf_files).iterdir():
            key = f"{str(fsf.stem)}"
            
            submission_string = SUBMISSION_STRING_TEMPLATE.format(
                fsf_file=fsf
            )

            # if python_path:
            #     submission_string += f"{python_path};"

            submission_strings[key] = submission_string

            if test_one:
                break
        return submission_strings


def _populate_batch_manager(batch_manager: BatchManager, 
                            submission_strings: dict):
    for key in submission_strings.keys():
        batch_manager.addjob(Job(key, submission_strings[key]))

    batch_manager.createsubmissionhead()
    batch_manager.compilejobstrings()