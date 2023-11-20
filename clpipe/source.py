from .config.options import ProjectOptions
from .utils import get_logger
import os
from pathlib import Path

from .job_manager import JobManagerFactory

STEP_NAME = "flywheel_sync"
FLYWHEEL_TEMP_DIR_NAME = "'<TemporaryDirectory '\\'''/"


def flywheel_sync(
    config_file,
    source_url=None,
    dropoff_dir=None,
    temp_dir=None,
    submit=False,
    debug=False,
):
    """Sync your project's DICOMs with Flywheel."""
    
    options: ProjectOptions = ProjectOptions.load(config_file)
    options.source.load_cli_args(
        dropoff_directory=dropoff_dir,
        temp_directory=temp_dir,
        source_url=source_url,
    )

    logger = get_logger(STEP_NAME, debug=debug, log_dir=options.get_logs_dir())

    if options.source.temp_directory == "":
        options.source.temp_directory = Path(options.project_directory) / "flywheel_tmp"
        logger.debug(f"Using default temp directory: {options.source.temp_directory}")

    if not Path(options.source.temp_directory).exists():
        Path(options.source.temp_directory).mkdir(parents=True)

    log_dir = Path(options.project_directory) / "logs" / "sync_logs"
    if not log_dir.exists:
        logger.debug(f"Creating log dir: {log_dir}")
        log_dir.mkdir()

    batch_manager = JobManagerFactory.get(
        batch_config=options.batch_config,
        output_directory=log_dir, 
        debug=debug,
        mem_use=options.source.mem_usage,
        time=options.source.time_usage,
        threads=options.source.core_usage
        )

    logger.debug(f"Using dropoff directory: {options.source.dropoff_directory}")
    logger.debug(f"Using source URL: {options.source.source_url}")
    logger.debug(f"Using temp directory: {options.source.temp_directory}")
    if options.source.commandline_opts != "":
        logger.debug(f"Added additional Flywheel options: {options.source.commandline_opts}")

    flywheel_generated_temp_dir = os.path.join(os.getcwd(), FLYWHEEL_TEMP_DIR_NAME)
    logger.debug(f"Temporary Directory: {flywheel_generated_temp_dir}")
    
    submission_string = f"fw sync --include dicom --tmp-path {options.source.temp_directory} {options.source.commandline_opts} {options.source.source_url} {options.source.dropoff_directory}; rm -r {flywheel_generated_temp_dir}"
    job_id = f"flywheel_sync_DICOM"

    batch_manager.add_job(job_name, submission_string)

    # job = Job(job_id, submission_string)
    # batch_manager.addjob(job)

    # batch_manager.compile_job_strings()

    if submit:
        batch_manager.submit_jobs()
    else:
        batch_manager.print_jobs()
