import pytest
from pathlib import Path
from clpipe.fmri_postprocess import fmri_postprocess

def test_fmriprep_process(config_file: Path):
    """ Check basic attempt to run fmriprep_process."""

    fmri_postprocess(config_file=config_file)
    assert True