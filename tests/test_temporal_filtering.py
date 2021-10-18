import sys
import logging
import pytest
import os

import numpy as np
import nibabel as nib

sys.path.append('../clpipe')
from clpipe.postprocutils.nodes import ButterworthFilter
import nipype.pipeline.engine as pe

logging.basicConfig(level=logging.INFO)


def test_butterworth_filter(tmp_path, sample_raw_image, workflow_base):
    filtered_path = tmp_path / "Test_Workflow" / "Butterworth_Filter" / "sample_raw_filtered.nii"
    
    butterworth_node = pe.Node(ButterworthFilter(in_file=sample_raw_image,
                                hp=.008,lp=-1,order=2,tr=2), name="Butterworth_Filter")
    workflow_base.add_nodes([butterworth_node])
    workflow_base.run()
    workflow_base.write_graph(dotfilename = tmp_path / "filteredflow", graph2use='flat')

    newImage = nib.load(filtered_path)
    print(newImage)

@pytest.mark.skip(reason="Not implemented")
def test_temporal_filter_low_pass(tmp_path):
    pass

@pytest.mark.skip(reason="Not implemented")
def test_temporal_filter_high_pass(tmp_path):
    pass

@pytest.mark.skip(reason="Not implemented")
def test_temporal_filter_band_pass(tmp_path):
    pass