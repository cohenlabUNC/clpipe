import pytest
from pathlib import Path
from clpipe.fmri_preprocess import fmriprep_process

def test_fmriprep_process_no_working(config_file: Path):
    """ Check basic attempt to run fmriprep_process without setting working dir."""

    with pytest.raises(SystemExit) as e:
        fmriprep_process(config_file=config_file)
    
    assert e.value.code == 1