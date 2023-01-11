from .config_json_parser import ClpipeConfigParser
from .utils import get_logger
import os
from pathlib import Path

from .batch_manager import BatchManager, Job

FLYWHEEL_TEMP_DIR_NAME = "'<TemporaryDirectory '\\'''/"

def sync_flywheel(config_file, source_url=None, sync_dir=None, submit=False, debug=False):
    """Sync your project's DICOMs with Flywheel."""
    
    config_parser = ClpipeConfigParser(config_file)
    config = config_parser.config

    if not sync_dir:
        try:
            sync_dir = config["DICOMToBIDSOptions"]["DICOMDirectory"]
        except KeyError:
            pass

    if not source_url:
        try:
            source_url = config["DICOMToBIDSOptions"]["SourceURL"]
        except KeyError:
            pass

    batch_config = config['BatchConfig']
    mem_usage = config['DICOMToBIDSOptions']['MemUsage']
    time_usage = config['DICOMToBIDSOptions']['TimeUsage']
    n_threads = config['DICOMToBIDSOptions']['CoreUsage']

    log_dir = Path(config["ProjectDirectory"]) / "logs" / "sync_logs"
    if not log_dir.exists:
        logger.debug(f"Creating log dir: {log_dir}")
        log_dir.mkdir()

    batch_manager = BatchManager(batch_config, log_dir, debug=debug)
    batch_manager.create_submission_head()
    batch_manager.update_mem_usage(mem_usage)
    batch_manager.update_time(time_usage)
    batch_manager.update_nthreads(n_threads)

    logger = get_logger("sync", debug=debug)

    logger.debug(f"Using sync dir: {sync_dir}")
    logger.debug(f"Using source URL: {source_url}")

    flywheel_generated_temp_dir = os.path.join(os.getcwd(), FLYWHEEL_TEMP_DIR_NAME)

    logger.info(f"Removing Temporary Directory: {flywheel_generated_temp_dir}")
    
    submission_string = f"fw sync --include dicom {source_url} {sync_dir}; rm -r {flywheel_generated_temp_dir}"
    job_id = f"sync_DICOM"

    job = Job(job_id, submission_string)

    batch_manager.addjob(job)
    
    batch_manager.compile_job_strings()

    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()