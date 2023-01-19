from .config_json_parser import ClpipeConfigParser
from .utils import get_logger
import os
from pathlib import Path

from .batch_manager import BatchManager, Job

FLYWHEEL_TEMP_DIR_NAME = "'<TemporaryDirectory '\\'''/"

def flywheel_sync(config_file, source_url=None, dropoff_dir=None, temp_dir=None, submit=False, debug=False):
    """Sync your project's DICOMs with Flywheel."""
    
    config_parser = ClpipeConfigParser(config_file)
    config = config_parser.config

    if not dropoff_dir:
        dropoff_dir = config["SourceOptions"]["DropoffDirectory"]

    if not source_url:
        source_url = config["SourceOptions"]["SourceURL"]

    if not temp_dir:
        temp_dir = config["SourceOptions"]["TempDirectory"]
        if temp_dir == "":
            temp_dir = Path(config["ProjectDirectory"]) / "flywheel_tmp"
    temp_dir = Path(temp_dir)

    try:
        cmd_line_opts = config['SourceOptions']['CommandLineOpts']
    except KeyError:
        cmd_line_opts = ""

    if not temp_dir.exists():
        temp_dir.mkdir(parents=True)
        
    batch_config = config['BatchConfig']
    mem_usage = config['SourceOptions']['MemUsage']
    time_usage = config['SourceOptions']['TimeUsage']
    n_threads = config['SourceOptions']['CoreUsage']

    log_dir = Path(config["ProjectDirectory"]) / "logs" / "sync_logs"
    if not log_dir.exists:
        logger.debug(f"Creating log dir: {log_dir}")
        log_dir.mkdir()

    batch_manager = BatchManager(batch_config, log_dir, debug=debug)
    batch_manager.create_submission_head()
    batch_manager.update_mem_usage(mem_usage)
    batch_manager.update_time(time_usage)
    batch_manager.update_nthreads(n_threads)

    logger = get_logger("flywheel_sync", debug=debug)

    logger.debug(f"Using sync dir: {dropoff_dir}")
    logger.debug(f"Using source URL: {source_url}")
    logger.debug(f"Using temp directory: {temp_dir}")
    if cmd_line_opts != "":
        logger.debug(f"Added additional Flywheel options: {cmd_line_opts}")

    flywheel_generated_temp_dir = os.path.join(os.getcwd(), FLYWHEEL_TEMP_DIR_NAME)

    logger.debug(f"Temporary Directory: {flywheel_generated_temp_dir}")
    
    submission_string = f"fw sync --include dicom --tmp-path {temp_dir} {cmd_line_opts} {source_url} {dropoff_dir}; rm -r {flywheel_generated_temp_dir}"
    job_id = f"flywheel_sync_DICOM"

    job = Job(job_id, submission_string)

    batch_manager.addjob(job)
    
    batch_manager.compile_job_strings()

    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()