import os, stat

from pathlib import Path

from .utils import get_logger, add_file_handler
from .config.options import ProjectOptions, DEFAULT_CONFIG_FILE_NAME
from .config.glm import GLMOptions
from .convert2bids import setup_dirs as setup_convert2bids_dirs
from .bids_validator import setup_dirs as setup_bids_validation_dirs
from .fmri_preprocess import setup_dirs as setup_preprocess_dirs
from .roi_extractor import setup_dirs as setup_roiextract_dirs
from .glm_prepare import setup_dirs as setup_glm_dirs

STEP_NAME = "project-setup"
DEFAULT_DICOM_DIR = "data_DICOMs"
DCM2BIDS_SCAFFOLD_TEMPLATE = "dcm2bids_scaffold -o {}"


DEFAULT_GLM_CONFIG_FILE_NAME = "glm_config.json"


class SourceDataError(ValueError):
    pass


def project_setup(
    project_title: str = "A Neuroimaging Project",
    project_dir: os.PathLike = os.getcwd(),
    source_data=None,
    move_source_data=False,
    symlink_source_data=False,
    debug=False,
):
    """Initialize a clpipe project.

    No values can come in as None except source_data.

    Args documented in corresponding CLI function.

    Raises:
        SourceDataError: Invalid source data was provided.
        NotImplementedError: Option requested is not implemented.
    """

    # Start up the logger, without file output until we get a project path
    logger = get_logger(STEP_NAME, debug=debug)

    # Create a default DICOM dir for source if no source given
    default_dicom_dir = os.path.join(project_dir, DEFAULT_DICOM_DIR)

    # Decide how to handle incoming source data options
    if symlink_source_data and move_source_data:
        raise SourceDataError("Cannot choose to both move and symlink the source data.")
    if symlink_source_data and not source_data:
        raise SourceDataError(
            "A source data path is required when using a symlinked source."
        )
    elif move_source_data and not source_data:
        raise SourceDataError("A source data path is required when moving source data.")
    elif source_data:
        logger.info(f"Referencing source data: {source_data}")
        source_data = Path(source_data).resolve()
    else:
        logger.info(f"No source data specified. Defaulting to: {default_dicom_dir}")
        source_data = default_dicom_dir
        Path(source_data).mkdir(exist_ok=False)

    logger.info(f"Starting project setup with title: {project_title}")

    logger.info(f"Creating new clpipe project in directory: {project_dir}")

    config: ProjectOptions = ProjectOptions()
    config.populate_project_paths(project_dir, source_data)
    config.project_title = project_title
    # Dump the now-populated config file
    config_file_path = os.path.join(project_dir, DEFAULT_CONFIG_FILE_NAME)
    logger.debug("Creating JSON config file")
    config.dump(config_file_path)

    # Setup directories for the first few steps
    setup_convert2bids_dirs(config)
    setup_bids_validation_dirs(config)
    setup_preprocess_dirs(config)
    setup_roiextract_dirs(config)

    # Setup GLM config and directories
    glm_config: GLMOptions = GLMOptions()
    glm_config.populate_project_paths(config_file_path)
    setup_glm_dirs(glm_config)
    glm_config.config_json_dump(config.project_directory, DEFAULT_GLM_CONFIG_FILE_NAME)

    # Add file output for logging
    add_file_handler(config.get_logs_dir())
    # Set permissions to clpipe.log file to allow for group write
    os.chmod(
        os.path.join(config.get_logs_dir(), "clpipe.log"),
        stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP,
    )

    if symlink_source_data:
        logger.info(f"Creating SymLink for source data to {default_dicom_dir}")
        os.symlink(source_data, default_dicom_dir)
    elif move_source_data:
        raise NotImplementedError("Option -move_source_data is not yet implemented.")

    # Create an empty BIDS directory
    os.system(DCM2BIDS_SCAFFOLD_TEMPLATE.format(config.convert2bids.bids_directory))
    logger.debug(
        f"Created empty BIDS directory at: {config.convert2bids.bids_directory}"
    )

    # Setup empty filler directories for analyses & scripting
    analyses_dir = os.path.join(project_dir, "analyses")
    os.makedirs(analyses_dir, exist_ok=True)
    logger.debug(f"Created empty analyses directory: {analyses_dir}")

    script_dir = os.path.join(project_dir, "scripts")
    os.makedirs(script_dir, exist_ok=True)
    logger.debug(f"Created empty scripts directory: {script_dir}")

    logger.info("Completed project setup")
