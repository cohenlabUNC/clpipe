import pytest
from pathlib import Path
from clpipe.fmri_postprocess import (
    fmri_postprocess,
    _fmri_postprocess_subject,
    STEP_NAME,
)
from clpipe.utils import get_logger
from clpipe.config_json_parser import ClpipeConfigParser
import os


def test_fmri_postprocess_basic(config_file_fmriprep: Path):
    """Check basic attempt to run fmriprep_process."""

    fmri_postprocess(config_file=config_file_fmriprep)


def test_fmri_postprocess_subject_basic(config_file_fmriprep: Path):
    """Check postprocessing a single subject."""
    config = ClpipeConfigParser()
    config.config_updater(config_file_fmriprep)

    logger = get_logger(STEP_NAME, debug=True)

    _fmri_postprocess_subject(config, "0", "2", logger, tr=2)
