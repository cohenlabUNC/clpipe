import sys
import logging
import pytest

import numpy as np
import nibabel as nib

sys.path.append('../clpipe')
from clpipe.postprocutils.workflows import build_10000_global_median_workflow, build_100_voxel_mean_workflow

logging.basicConfig(level=logging.INFO)

@pytest.mark.skip(reason="Needs refactor")
def test_calculate_10000_global_median(tmp_path, random_nii):
    out_path = tmp_path / "normalized.nii.gz"
    calculate_10000_global_median(random_nii, out_path, base_dir=tmp_path)

    # Load random nii data and a mask
    random_nii_data = nib.load(random_nii).get_fdata()
    normalized_data = nib.load(out_path).get_fdata()

    median = np.median(random_nii_data)
    rescale_factor = 10000 / median
    mul_rescale = random_nii_data * rescale_factor

    # Ensure the calculation for a single voxel matches a voxel from the image dataset
    assert round(mul_rescale[0][0][0][0], 2) == round(normalized_data[0][0][0][0], 2)

@pytest.mark.skip(reason="Needs refactor")
def test_calculate_10000_global_median_masked(tmp_path, random_nii, random_nii_mask):
    out_path = tmp_path / "normalized.nii.gz"
    calculate_10000_global_median(random_nii, out_path, mask_path=random_nii_mask, base_dir=tmp_path,
        crashdump_dir=tmp_path)

    # Load random nii data and a mask
    random_nii_data = nib.load(random_nii).get_fdata()
    normalized_data = nib.load(out_path).get_fdata()

    median = np.median(random_nii_data)
    rescale_factor = 10000 / median
    mul_rescale = random_nii_data * rescale_factor

    # Prove that the mask is included in median calculation
    assert round(mul_rescale[0][0][0][0], 4) != round(normalized_data[0][0][0][0], 4)

def test_calculate_100_voxel_mean_wf(tmp_path, sample_raw_image):
    out_path = tmp_path / "normalized.nii.gz"
    wf = build_100_voxel_mean_workflow(in_file=sample_raw_image, out_file=out_path, base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.run()
    wf.write_graph(dotfilename = tmp_path / "calc100voxelMeanFlow", graph2use='flat')

    assert True

def test_calculate_100_voxel_mean(tmp_path, random_nii):
    out_path = tmp_path / "normalized.nii.gz"
    wf = build_100_voxel_mean_workflow(in_file=random_nii, out_file=out_path, base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.run()

    random_nii_data = nib.load(random_nii).get_fdata()
    normalized_data = nib.load(out_path).get_fdata()

    # Ensure the shape is 4d
    assert len(normalized_data.shape) == 4

    mean = np.average(random_nii_data, axis=3)[0]
    mul100 = random_nii_data[0][0][0][0] * 100
    div_mean = mul100 / mean

    # Ensure the calculation for a single voxel matches a voxel from the image dataset
    assert round(div_mean[0][0], 2) == round(normalized_data[0][0][0][0], 2)