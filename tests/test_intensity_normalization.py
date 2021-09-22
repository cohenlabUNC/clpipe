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

@pytest.fixture(scope="module")
def clpipe_normalized_dir(clpipe_fmriprep_dir):
    """Fixture which adds a normalization output folder"""

    normalized_folder = clpipe_fmriprep_dir / "data_normalized"
    normalized_folder.mkdir()
    
    return clpipe_fmriprep_dir

@pytest.fixture(scope="module")
def normalization_config(clpipe_config_default, clpipe_normalized_dir):
    """Fixture which sets up an intensity normalization enabled configuration object."""
    target_dir: Path = clpipe_normalized_dir / "data_fmriprep" / "fmriprep"
    output_dir: Path = clpipe_normalized_dir / "data_normalized"

    clpipe_config_default.config['IntensityNormalizationOptions']['TargetDirectory'] = str(target_dir)
    clpipe_config_default.config['IntensityNormalizationOptions']['OutputDirectory'] = str(output_dir)
    clpipe_config_default.config['IntensityNormalizationOptions']['TargetSuffix'] = "preproc_bold.nii.gz"
    clpipe_config_default.config['IntensityNormalizationOptions']['OutputSuffix'] = "normalized.nii.gz"
    clpipe_config_default.config['IntensityNormalizationOptions']['Method'] = "10000_globalmedian"

    return clpipe_config_default

def test_intensity_normalization_cli_10000_global_median(normalization_config, clpipe_fmriprep_dir):
    runner = CliRunner()
    result = runner.invoke(
    intensity_normalization_cli, 
    [
        '-method', "10000_globalmedian", 
        '-config_file', clpipe_fmriprep_dir / "clpipe_config.json",
        '-target_dir', normalization_config.config['IntensityNormalizationOptions']['TargetDirectory'],
        '-output_dir', normalization_config.config['IntensityNormalizationOptions']['OutputDirectory'], 
        '-output_suffix', normalization_config.config['IntensityNormalizationOptions']['OutputSuffix'], 
        '-log_dir', LOG_DIR_PATH,
        '-submit', True, 
        '-batch', False, 
        '-debug', True, 
    ])

    assert result.exit_code == 0

def test_intensity_normalization_cli_100_voxel_mean(normalization_config, clpipe_fmriprep_dir):
    runner = CliRunner()
    result = runner.invoke(
    intensity_normalization_cli, 
    [
        '-method', "100_voxelmean", 
        '-config_file', clpipe_fmriprep_dir / "clpipe_config.json",
        '-target_dir', normalization_config.config['IntensityNormalizationOptions']['TargetDirectory'],
        '-output_dir', normalization_config.config['IntensityNormalizationOptions']['OutputDirectory'], 
        '-output_suffix', normalization_config.config['IntensityNormalizationOptions']['OutputSuffix'], 
        '-log_dir', LOG_DIR_PATH,
        '-submit', True, 
        '-batch', False, 
        '-debug', True, 
    ])

    assert result.exit_code == 0

def test_intensity_normalization_cli_None():
    runner = CliRunner()
    result = runner.invoke(
    intensity_normalization_cli, 
    [
        '-method', "", 
        '-config_file', "",
        '-target_dir', "",
        '-output_dir', "", 
        '-output_suffix', "", 
        '-log_dir', "",
        '-submit', False, 
        '-batch', False, 
        '-debug', True, 
    ])

    assert result.exit_code != 0


def test_intensity_normalization_100_voxel_mean(normalization_config, clpipe_fmriprep_dir):
    """Must create data_normalization folder."""
    intensity_normalization(
                            subjects=list(range(0, 8)),
                            target_dir=normalization_config.config['IntensityNormalizationOptions']['TargetDirectory'],
                            output_dir=normalization_config.config['IntensityNormalizationOptions']['OutputDirectory'],
                            output_suffix=normalization_config.config['IntensityNormalizationOptions']['OutputSuffix'],
                            config_file=clpipe_fmriprep_dir / "clpipe_config.json",
                            method="100_voxelmean"
                            )

    count = 0
    for subject in (Path(normalization_config.config['IntensityNormalizationOptions']['OutputDirectory']) / "100_voxelmean").iterdir():
        count += 1

    assert count == 8

def test_intensity_normalization_10000_global_median(normalization_config, clpipe_fmriprep_dir):
    """Must create data_normalization folder."""
    intensity_normalization(
                            subjects=list(range(0, 8)),
                            target_dir=normalization_config.config['IntensityNormalizationOptions']['TargetDirectory'],
                            output_dir=normalization_config.config['IntensityNormalizationOptions']['OutputDirectory'],
                            output_suffix=normalization_config.config['IntensityNormalizationOptions']['OutputSuffix'],
                            config_file=clpipe_fmriprep_dir / "clpipe_config.json"
                            )

    count = 0
    for subject in (Path(normalization_config.config['IntensityNormalizationOptions']['OutputDirectory']) / "10000_globalmedian").iterdir():
        count += 1

    assert count == 8

def test_normalize_subject_10000_global_median(normalization_config):
    """Asserts that intensity_normalization() creates a normalized image using the 10000 global median method
    and saves the output using the configurations provided in the configuration object. """
    normalize_subject(normalization_config, 'sub-0')

    expected_path = Path(normalization_config.config['IntensityNormalizationOptions']['OutputDirectory']) \
        / "10000_globalmedian" \
        / "sub-0" \
        / "sub-0_task-rest_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold_normalized.nii.gz"

    assert expected_path.exists(), f"Expected path {expected_path} not found."

def test_normalize_subject_100_voxel_mean(normalization_config):
    """Asserts that intensity_normalization() creates a normalized image using the 100 voxel mean method
    and saves the output using the configurations provided in the configuration object. """

    # Override the default method '10000 global median'
    normalization_config.config['IntensityNormalizationOptions']['Method'] = "100_voxelmean"

    normalize_subject(normalization_config, 'sub-0')

    expected_path = Path(normalization_config.config['IntensityNormalizationOptions']['OutputDirectory']) \
        / "100_voxelmean" \
        / "sub-0" \
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