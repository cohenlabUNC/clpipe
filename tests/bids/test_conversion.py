import pytest

from clpipe.bids_conversion import dcm2bids_wrapper

def test_dcm2bids(clpipe_dir):
    dicom_dir = clpipe_dir / "data_DICOMs"

    assert True
