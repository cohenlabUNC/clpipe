import pytest

import nipype.pipeline.engine as pe
import nibabel as nib
from nilearn import plotting
from nilearn.image import load_img, index_img

from clpipe.postprocutils.workflows import *

def test_spatial_smoothing_wf(tmp_path, sample_raw_image, sample_raw_image_mask, plot_img):
    out_path = tmp_path / "smoothed.nii.gz"
    wf = build_spatial_smoothing_workflow(in_file=sample_raw_image, out_file=out_path, fwhm_mm=6, 
        mask_path=sample_raw_image_mask, base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.run()
    wf.write_graph(dotfilename = tmp_path / "spatialSmoothFlow", graph2use='colored')

    if plot_img:
        image = load_img(str(out_path))
        image_slice = index_img(image, 1)
        plotting.plot_img(image_slice, output_file= str(tmp_path / "smoothed.png"))
    
    assert True

def test_calculate_100_voxel_mean_wf(tmp_path, sample_raw_image, plot_img):
    out_path = tmp_path / "normalized_100vm.nii.gz"
    wf = build_100_voxel_mean_workflow(in_file=sample_raw_image, out_file=out_path, base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.run()
    wf.write_graph(dotfilename = tmp_path / "calc100voxelMeanFlow", graph2use='colored')

    if plot_img:
        image = load_img(str(out_path))
        image_slice = index_img(image, 1)
        plotting.plot_img(image_slice, output_file= str(tmp_path / "normalized_100vm.png"))

    assert True

def test_calculate_10000_global_median_wf(tmp_path, sample_raw_image, sample_raw_image_mask, plot_img):
    out_path = tmp_path / "normalized_10000gm.nii.gz"
    
    wf = build_10000_global_median_workflow(in_file=sample_raw_image, out_file=out_path, mask_file=sample_raw_image_mask, base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.run()
    wf.write_graph(dotfilename = tmp_path / "calc10000globalMedianFlow", graph2use='colored')

    if plot_img:
        image = load_img(str(out_path))
        image_slice = index_img(image, 1)
        plotting.plot_img(image_slice, output_file= str(tmp_path / "normalized_10000gm.png"))

    assert True
    
def test_butterworth_filter_wf(tmp_path, sample_raw_image, plot_img):
    filtered_path = tmp_path / "sample_raw_filtered.nii"

    wf = build_butterworth_filter_workflow(hp=.008, lp=-1, tr=2, order=2, in_file=sample_raw_image, out_file=filtered_path, 
        base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.run()
    wf.write_graph(dotfilename = tmp_path / "filteredflow", graph2use='colored')

    if plot_img:
        image = load_img(str(filtered_path))
        image_slice = index_img(image, 1)
        plotting.plot_img(image_slice, output_file= str(tmp_path / "filtered.png"))
    
    assert True
