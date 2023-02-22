import pytest
from pathlib import Path
from clpipe.fmri_preprocess import fmriprep_process

def test_fmriprep_process(config_file: Path):
    """ Check basic attempt to run fmriprep_process."""

    fmriprep_process(config_file=config_file)
    assert True