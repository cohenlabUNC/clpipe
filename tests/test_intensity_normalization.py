import pathlib
import sys
import pytest
import typing

from click.testing import CliRunner
import numpy as np
import nibabel as nib

sys.path.append('../clpipe')
from clpipe.intensity_normalization import *
from clpipe.config_json_parser import ClpipeConfigParser
from conftest import NUM_SUBJECTS

CONFIG_FILE_PATH = "clpipe_config.json"
FMRI_PREPPED_SUFFIX = "_boldref"
LOG_DIR_PATH = "logs"

logging.basicConfig(level=logging.INFO)

@pytest.fixture()
def clpipe_normalized_dir(clpipe_fmriprep_dir):
    """Fixture which adds normalization output folders"""

    for sub_num in range(NUM_SUBJECTS):
        voxel_mean_folder = clpipe_fmriprep_dir / "data_normalized" / "100_voxel_mean" / f"sub-{sub_num}"
        voxel_mean_folder.mkdir(parents=True)
        global_median_folder = clpipe_fmriprep_dir / "data_normalized" / "10000_global_median" / f"sub-{sub_num}"
        global_median_folder.mkdir(parents=True)
    
    return clpipe_fmriprep_dir

@pytest.mark.skip(reason="Not yet implemented")
def test_intensity_normalization_cli_10000_global_median():
    runner = CliRunner()
    result = runner.invoke(
    intensity_normalization_cli, 
    [
        '-rescaling_method', RESCALING_10000_GLOBALMEDIAN, 
        '-config_file', CONFIG_FILE_PATH,
        '-target_dir', TARGET_DIR_PATH,
        '-output_dir', OUTPUT_DIR_PATH, 
        '-output_suffix', OUTPUT_SUFFIX, 
        '-log_dir', LOG_DIR_PATH,
        '-submit', True, 
        '-batch', False, 
        '-debug', True, 
    ])

    if result.exit_code != 0:
        raise Exception(result.exception)

@pytest.mark.skip(reason="Not yet implemented")
def test_intensity_normalization_cli_100_voxel_mean():
    runner = CliRunner()
    result = runner.invoke(
    intensity_normalization_cli, 
    [
        '-rescaling_method', RESCALING_100_VOXELMEAN, 
        '-config_file', CONFIG_FILE_PATH,
        '-target_dir', TARGET_DIR_PATH,
        '-output_dir', OUTPUT_DIR_PATH, 
        '-output_suffix', OUTPUT_SUFFIX, 
        '-log_dir', LOG_DIR_PATH,
        '-submit', True, 
        '-batch', False, 
        '-debug', True, 
    ])

    if result.exit_code != 0:
        raise Exception(result.exception)

@pytest.mark.skip(reason="Not yet implemented")
def test_intensity_normalization_None():
    runner = CliRunner()
    result = runner.invoke(
    intensity_normalization_cli, 
    [
        '-rescaling_method', "", 
        '-config_file', "",
        '-target_dir', "",
        '-output_dir', "", 
        '-output_suffix', "", 
        '-log_dir', "",
        '-submit', False, 
        '-batch', False, 
        '-debug', True, 
    ])

    if result.exit_code != 0:
        raise Exception(result.exception)

@pytest.mark.skip(reason="Not yet implemented")
def test_intensity_normalization_10000_global_median():
    intensity_normalization(
                            target_dir=TARGET_DIR_PATH,
                            output_dir=OUTPUT_DIR_PATH,
                            config_file=clpipe_fmriprep_dir / "clpipe_config.json"
                            )

def test_normalize_subject_100_voxel_mean(clpipe_normalized_dir):
    """Asserts that intensity_normalization() creates a normalized image using the 100 voxel mean method
    and saves the output using the configurations provided in clpipe_config.json """
    
    subject_path: Path = clpipe_normalized_dir / "data_fmriprep" / "fmriprep" / "sub-0" / "func"
    output_dir: Path = clpipe_normalized_dir / "data_normalized" / "100_voxel_mean" / "sub-0"

    normalize_subject(subject_path, output_dir,
                        method=calculate_100_voxel_mean)

    expected_path = output_dir \
        / "sub-0_task-rest_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold_normalized.nii.gz"

    assert expected_path.exists(), f"Expected path {expected_path} not found."

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

def test_calculate_10000_global_median_masked(tmp_path, random_nii, random_nii_mask):
    out_path = tmp_path / "normalized.nii.gz"
    calculate_10000_global_median(random_nii, out_path, mask_path=random_nii_mask, base_dir=tmp_path)

    # Load random nii data and a mask
    random_nii_data = nib.load(random_nii).get_fdata()
    normalized_data = nib.load(out_path).get_fdata()

    median = np.median(random_nii_data)
    rescale_factor = 10000 / median
    mul_rescale = random_nii_data * rescale_factor

    # Prove that the mask is included in median calculation
    assert round(mul_rescale[0][0][0][0], 4) != round(normalized_data[0][0][0][0], 4)

def test_calculate_100_voxel_mean(tmp_path, random_nii):
    out_path = tmp_path / "normalized.nii.gz"
    calculate_100_voxel_mean(random_nii, out_path, base_dir=tmp_path)
    
    random_nii_data = nib.load(random_nii).get_fdata()
    normalized_data = nib.load(out_path).get_fdata()

    # Ensure the shape is 4d
    assert len(normalized_data.shape) == 4

    mean = np.average(random_nii_data, axis=3)[0]
    mul100 = random_nii_data[0][0][0][0] * 100
    div_mean = mul100 / mean

    # Ensure the calculation for a single voxel matches a voxel from the image dataset
    assert round(div_mean[0][0], 2) == round(normalized_data[0][0][0][0], 2)