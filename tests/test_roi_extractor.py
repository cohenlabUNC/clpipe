import pytest

from clpipe.roi_extractor import fmri_roi_extraction

def test_fmri_roi_extraction(config_file_postproc2):
    """Basic test of roi_extraction using single run."""
    fmri_roi_extraction(subjects=["1"], single=True, 
        config_file=config_file_postproc2, debug=True)

def test_fmri_roi_extraction_legacy(config_file_postproc2_legacy_fmriprep):
    """Basic test of roi_extraction using single run
        on fmriprep version < 21"""
    fmri_roi_extraction(subjects=["1"], single=True, 
        config_file=config_file_postproc2_legacy_fmriprep, debug=True)

