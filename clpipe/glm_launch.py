import os
import sys
from pathlib import Path

from .config.glm import *
from .job_manager import JobManagerFactory
from .utils import get_logger

DEFAULT_BATCH_CONFIG_PATH = "slurmUNCConfig.json"

DEFAULT_L1_MEMORY_USAGE = "10G"
DEFAULT_L1_TIME_USAGE = "10:00:00"
DEFAULT_L1_N_THREADS = "4"

DEFAULT_L2_MEMORY_USAGE = "5G"
DEFAULT_L2_TIME_USAGE = "5:00:00"
DEFAULT_L2_N_THREADS = "4"

STEP_NAME = "glm-launch"

# Unset PYTHONPATH to ensure FSL uses its own internal python
#   libraries
SUBMISSION_STRING_TEMPLATE = "unset PYTHONPATH; feat {fsf_file}"
DEPRECATION_MSG = "Using deprecated GLM setup file."


def glm_launch(
    glm_config_file: str = None,
    level: int = L1,
    model: str = None,
    test_one: bool = False,
    submit: bool = False,
    debug: bool = False,
):
    glm_config = GLMOptions(glm_config_file)

    logger = get_logger(
        STEP_NAME, debug=debug, log_dir=glm_config.parent_options.get_logs_dir()
    )

    if level in VALID_L1:
        level = "L1"
        setup = "Level1Setups"
    elif level in VALID_L2:
        level = "L2"
        setup = "Level2Setups"
    else:
        logger.error(f"Level must be {L1} or {L2}")
        sys.exit(1)

    logger.info(f"Setting up {level} .fsf launch using model: {model}")

    block = [x for x in glm_config.config[setup] if x["ModelName"] == str(model)]
    if len(block) is not 1:
        logger.error("Model not found, or multiple entries found.")
        sys.exit(1)
    model_options = block[0]

    try:
        batch_options = model_options["BatchOptions"]

        memory_usage = batch_options["MemoryUsage"]
        time_usage = batch_options["TimeUsage"]
        n_threads = int(batch_options["NThreads"])
        batch_config_path = glm_config.parent_options.batch_config_path
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

    batch_manager = JobManagerFactory.get(
        batch_config=batch_config_path,
        output_directory=log_dir,
        mem_use=memory_usage,
        time=time_usage,
        threads=n_threads,
        email=email
    )

    submission_strings = _create_submission_strings(fsf_dir, test_one=test_one)

    num_jobs = len(submission_strings)

    for key in submission_strings.keys():
        batch_manager.add_job(key, submission_strings[key])

    if submit:
        logger.info(f"Running {num_jobs} job(s) in batch mode")
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()
    sys.exit(0)

def _create_submission_strings(fsf_files: os.PathLike, test_one: bool = False):
    submission_strings = {}

    for fsf in Path(fsf_files).iterdir():
        key = f"{str(fsf.stem)}"

        submission_string = SUBMISSION_STRING_TEMPLATE.format(fsf_file=fsf)

        # if python_path:
        #     submission_string += f"{python_path};"

        submission_strings[key] = submission_string

        if test_one:
            break
    return submission_strings
