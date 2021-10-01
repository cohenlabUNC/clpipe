import sys
import logging
import pytest

import numpy as np
import nibabel as nib

sys.path.append('../clpipe')
from clpipe.hngprep import temporal_filter

logging.basicConfig(level=logging.INFO)


def test_temporal_filter(tmp_path, random_nii):
    filtered_path = tmp_path / "filtered.nii"
    temporal_workflow = temporal_filter(random_nii, filtered_path)
    temporal_workflow.run()
    
    assert True

@pytest.mark.skip(reason="Not implemented")
def test_temporal_filter_low_pass(tmp_path):
    pass

@pytest.mark.skip(reason="Not implemented")
def test_temporal_filter_high_pass(tmp_path):
    pass

@pytest.mark.skip(reason="Not implemented")
def test_temporal_filter_band_pass(tmp_path):
    pass