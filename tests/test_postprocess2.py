import pytest

import nipype.pipeline.engine as pe
import nibabel as nib
from nilearn import plotting
from nilearn.image import load_img, index_img

from clpipe.postprocutils.workflows import *

def test_postprocess2_wf(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(postprocessing_config, sample_raw_image, out_path, 2, mask_file=sample_raw_image_mask,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True