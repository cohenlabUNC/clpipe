import pytest
from clpipe.fmri_preprocess import fmriprep_process

def test_fmriprep_process(config_file):
    """ Check basic attempt to run fmriprep_process."""

    fmriprep_process(config_file=config_file)
    assert True