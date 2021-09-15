import sys
import pytest

from click.testing import CliRunner
import numpy as np
import nibabel as nib

sys.path.append('../clpipe')
from clpipe.intensity_normalization import *
from clpipe.config_json_parser import ClpipeConfigParser

CONFIG_FILE_PATH = "clpipe_config.json"
FMRI_PREPPED_SUFFIX = "_boldref"
LOG_DIR_PATH = "logs"

logging.basicConfig(level=logging.INFO)

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
                            )

def test_intensity_normalization_100_voxel_mean(clpipe_fmriprep_dir):
    """Asserts that intensity_normalization() creates a normalized image using the 100 voxel mean method
    and saves the output using the configurations provided in clpipe_config.json """

    config = ClpipeConfigParser()
    
    target_suffix = config.config["IntensityNormalizationOptions"]["TargetSuffix"]
    output_path = Path(config.config["IntensityNormalizationOptions"]["OutputDirectory"])
    output_suffix = config.config["IntensityNormalizationOptions"]["OutputSuffix"]
    
    intensity_normalization(subjects=[1],
                            method="100_voxelmean",
                            config_file=clpipe_fmriprep_dir / "clpipe_config.json"
                            )

    expected_path = output_path / "sub-1_task-rest_run-1_" + target_suffix + output_suffix
    
    assert expected_path.exists(), f"Expected path {expected_path} not found."

def test_calculate_10000_global_median(tmp_path, random_nii):
    out_path = tmp_path / "normalized.nii.gz"
    calculate_10000_global_median(random_nii, out_path, base_dir=tmp_path)

    random_nii_data = nib.load(random_nii).get_fdata()
    normalized_data = nib.load(out_path).get_fdata()

    # Ensure the shape is 4d
    assert len(normalized_data.shape) == 4

    median = np.median(random_nii_data)
    rescale_factor = 10000 / median
    mul_rescale = random_nii_data * rescale_factor

    # Ensure the calculation for a single voxel matches a voxel from the image dataset
    assert round(mul_rescale[0][0][0][0], 2) == round(normalized_data[0][0][0][0], 2)


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