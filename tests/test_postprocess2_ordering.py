import pytest

import nipype.pipeline.engine as pe
import nibabel as nib
from nilearn import plotting
from nilearn.image import load_img, index_img

from clpipe.postprocutils.workflows import *

def test_postprocess_wf(clpipe_config_default, tmp_path, sample_raw_image, sample_raw_image_mask, plot_img):
    out_path = tmp_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow("postproc_test", sample_raw_image, out_path, 
        processing_steps=["temporal_filtering", "intensity_normalization", "spatial_smoothing"], base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.write_graph(dotfilename = tmp_path / "postProcessSubjectFlow", graph2use='colored')
    wf.run()

    if plot_img:
        image = load_img(str(out_path))
        image_slice = index_img(image, 1)
        plotting.plot_img(image_slice, output_file= str(tmp_path / "postProcessed.png"))

    assert True

def test_postprocess_wf_order2(clpipe_config_default, tmp_path, sample_raw_image, sample_raw_image_mask, plot_img):
    out_path = tmp_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow("postproc_test", sample_raw_image, out_path, 
        processing_steps=["intensity_normalization", "temporal_filtering", "spatial_smoothing"], base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.write_graph(dotfilename = tmp_path / "postProcessSubjectFlow", graph2use='colored')
    wf.run()

    if plot_img:
        image = load_img(str(out_path))
        image_slice = index_img(image, 1)
        plotting.plot_img(image_slice, output_file= str(tmp_path / "postProcessed.png"))

    assert True

def test_postprocess_wf_order3(clpipe_config_default, tmp_path, sample_raw_image, sample_raw_image_mask, plot_img):
    out_path = tmp_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow("postproc_test", sample_raw_image, out_path, 
        processing_steps=["spatial_smoothing", "temporal_filtering", "intensity_normalization"], base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.write_graph(dotfilename = tmp_path / "postProcessSubjectFlow", graph2use='colored')
    wf.run()

    if plot_img:
        image = load_img(str(out_path))
        image_slice = index_img(image, 1)
        plotting.plot_img(image_slice, output_file= str(tmp_path / "postProcessed.png"))

    assert True

def test_postprocess_wf_order4(clpipe_config_default, tmp_path, sample_raw_image, sample_raw_image_mask, plot_img):
    out_path = tmp_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow("postproc_test", sample_raw_image, out_path, 
        processing_steps=["temporal_filtering", "intensity_normalization"], base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.write_graph(dotfilename = tmp_path / "postProcessSubjectFlow", graph2use='colored')
    wf.run()

    if plot_img:
        image = load_img(str(out_path))
        image_slice = index_img(image, 1)
        plotting.plot_img(image_slice, output_file= str(tmp_path / "postProcessed.png"))

    assert True

def test_postprocess_wf_order5(clpipe_config_default, tmp_path, sample_raw_image, sample_raw_image_mask, plot_img):
    out_path = tmp_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow("postproc_test", sample_raw_image, out_path, 
        processing_steps=["intensity_normalization", "temporal_filtering"], base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.write_graph(dotfilename = tmp_path / "postProcessSubjectFlow", graph2use='colored')
    wf.run()

    if plot_img:
        image = load_img(str(out_path))
        image_slice = index_img(image, 1)
        plotting.plot_img(image_slice, output_file= str(tmp_path / "postProcessed.png"))

    assert True
