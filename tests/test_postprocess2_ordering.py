import pytest

import nipype.pipeline.engine as pe
import nibabel as nib
from nilearn import plotting
from nilearn.image import load_img, index_img

from clpipe.postprocutils.workflows import *

def test_postprocess_wf_order_1(artifact_dir, request, sample_raw_image, sample_raw_image_mask, plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(sample_raw_image, out_path, mask_file=sample_raw_image_mask,
        processing_steps=["temporal_filtering", "intensity_normalization", "spatial_smoothing"], base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True

def test_postprocess_wf_order_2(artifact_dir, request, sample_raw_image, sample_raw_image_mask, plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(sample_raw_image, out_path, mask_file=sample_raw_image_mask,
        processing_steps=["intensity_normalization", "temporal_filtering", "spatial_smoothing"], base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True

def test_postprocess_wf_order_3(artifact_dir, request, sample_raw_image, sample_raw_image_mask, plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(sample_raw_image, out_path, mask_file=sample_raw_image_mask,
        processing_steps=["spatial_smoothing", "temporal_filtering", "intensity_normalization"], base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True

def test_postprocess_wf_order_4(artifact_dir, request, sample_raw_image, sample_raw_image_mask, plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(sample_raw_image, out_path, mask_file=sample_raw_image_mask,
        processing_steps=["temporal_filtering", "intensity_normalization"], base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True

def test_postprocess_wf_order_5(artifact_dir, request, sample_raw_image, sample_raw_image_mask, plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(sample_raw_image, out_path, mask_file=sample_raw_image_mask,
        processing_steps=["intensity_normalization", "spatial_smoothing"], base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True

def test_postprocess_wf_order_6(artifact_dir, request, sample_raw_image, sample_raw_image_mask, plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(sample_raw_image, out_path, mask_file=sample_raw_image_mask,
        processing_steps=["temporal_filtering", "spatial_smoothing"], base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True