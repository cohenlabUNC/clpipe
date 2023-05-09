import pytest

from clpipe.roi_extractor import fmri_roi_extraction

def test_fmri_roi_extraction(config_file_fmriprep):
    """Basic test of roi_extraction using single run."""
    fmri_roi_extraction(subjects=["1"], single=True, 
        config_file=config_file_fmriprep, debug=True)