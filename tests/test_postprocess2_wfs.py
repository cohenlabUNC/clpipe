import pytest

import nipype.pipeline.engine as pe
import nibabel as nib
from nilearn import plotting
from nilearn.image import load_img, index_img
import os
from pathlib import Path

from clpipe.postprocutils.workflows import *

def test_spatial_smoothing_wf(artifact_dir, request, sample_raw_image, sample_raw_image_mask, plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    
    out_path = test_path / "smoothed.nii.gz"
    wf = build_spatial_smoothing_workflow(in_file=sample_raw_image, out_file=out_path, fwhm_mm=6, 
        mask_path=sample_raw_image_mask, base_dir=test_path, crashdump_dir=test_path)
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "filteredflow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(out_path, "smoothed.png")
    
    assert True

def test_spatial_smoothing_wf_no_mask(artifact_dir, request, sample_raw_image, plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    
    out_path = test_path / "smoothed.nii.gz"
    wf = build_spatial_smoothing_workflow(in_file=sample_raw_image, out_file=out_path, fwhm_mm=6, 
        base_dir=test_path, crashdump_dir=test_path)
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "filteredflow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(out_path, "smoothed.png")
    
    assert True

def test_calculate_100_voxel_mean_wf(artifact_dir, sample_raw_image, plot_img, write_graph, request, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    out_path = test_path / "normalized_100vm.nii.gz"
    wf = build_100_voxel_mean_workflow(in_file=sample_raw_image, out_file=out_path, base_dir=test_path, crashdump_dir=test_path)
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "calc100voxelMeanFlow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(out_path, "normalized_100vm.png")

    assert True

def test_calculate_10000_global_median_wf(artifact_dir, sample_raw_image, sample_raw_image_mask, plot_img, write_graph, request, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    
    out_path = test_path / "normalized_10000gm.nii.gz"
    
    wf = build_10000_global_median_workflow(in_file=sample_raw_image, out_file=out_path, mask_file=sample_raw_image_mask, base_dir=test_path, crashdump_dir=test_path)
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "calc10000globalMedianFlow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(out_path, "normalized_10000gm.png")

    assert True
    
def test_butterworth_filter_wf(artifact_dir, sample_raw_image, plot_img, write_graph, request, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    
    filtered_path = test_path / "sample_raw_filtered.nii"

    wf = build_butterworth_filter_workflow(hp=.008, lp=-1, tr=2, order=2, in_file=sample_raw_image, out_file=filtered_path, 
        base_dir=test_path, crashdump_dir=test_path)
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "filteredflow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(filtered_path, "filtered.png")
    
    assert True

def test_confound_regression_wf(artifact_dir, sample_raw_image, sample_postprocessed_confounds, sample_raw_image_mask, plot_img, write_graph, request, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    regressed_path = test_path / "sample_raw_regressed.nii"

    wf = build_confound_regression_workflow(confound_file = sample_postprocessed_confounds, in_file=sample_raw_image, out_file=regressed_path, 
        mask_file=sample_raw_image_mask, base_dir=test_path, crashdump_dir=test_path)
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "filteredflow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(filtered_path, "filtered.png")
