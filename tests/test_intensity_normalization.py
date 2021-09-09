import sys
import pytest
from pathlib import Path

from click.testing import CliRunner
import numpy as np
import nibabel as nib

sys.path.append('../clpipe')
from clpipe.intensity_normalization import *
from clpipe.project_setup import project_setup

CONFIG_FILE_PATH = "clpipe_config.json"
TARGET_DIR_PATH = "data_fmriprep"
OUTPUT_DIR_PATH = "data_postproc/postproc_normalize"
OUTPUT_SUFFIX = "_normalized"
LOG_DIR_PATH = "logs"
PROJECT_TITLE = "test_project"
NUM_SUBJECTS = 8
DEFAULT_RANDOM_NII_DIMS = (3, 3, 3, 12)

logging.basicConfig(level=logging.INFO)

@pytest.fixture(scope="session")
def clpipe_dir(tmp_path_factory):
    #TODO: abstract this out for use in future test modules
    """Fixture which provides a temporary clpipe project folder."""
    proj_path = tmp_path_factory.mktemp(PROJECT_TITLE)
    
    raw_data = Path(proj_path / "data_DICOMs")
    raw_data.mkdir(parents=True, exist_ok=True)

    # Use the clpipe CLI to setup project
    runner = CliRunner()
    result = runner.invoke(
        project_setup, 
        [
            '-project_title', PROJECT_TITLE, 
            '-project_dir', str(proj_path),
            '-source_data', str(raw_data), 
        ]
    )

    # Raise any exceptions from the CLI
    if result.exit_code != 0:
        raise Exception(result.exception)

    return proj_path

@pytest.fixture
def clpipe_bids_dir(clpipe_dir):
    """Fixture which adds some subject folders to data_BIDS."""

    for sub_num in range(NUM_SUBJECTS):
            subject_folder = clpipe_dir / "data_BIDS" / f"sub-{sub_num}"
            subject_folder.mkdir()

    return clpipe_dir

@pytest.fixture
def clpipe_fmriprep_dir(clpipe_dir):
    """Fixture which adds fmriprep subject folders to data_fmriprep."""
    for sub_num in range(NUM_SUBJECTS):
        subject_folder = clpipe_dir / "data_fmriprep" / f"sub-{sub_num}"
        subject_folder.mkdir()
    
    return clpipe_dir

def generate_random_nii(dims: tuple=DEFAULT_RANDOM_NII_DIMS, low: int=0, high: int=10) -> nib.Nifti1Image:
    """Creates a simple nii image with the given dimensions.

    Args:
        dims (tuple): A 3d or 4d tuple representing dimensions of the nii.
        low (int): The floor generated voxel intensity.
        high (int): The ceiling generated voxel intensity.

    Returns:
        nib.Nifti1Image: A random nii image.
    """
    size = 1
    for x in dims:
        size *= x

    affine = np.diag([1 for x in dims])

    array_data = np.random.randint(low, high=high, size=size, dtype=np.int16).reshape(dims)
    image = nib.Nifti1Image(array_data, affine)

    return image

@pytest.fixture
def random_nii(tmp_path):
    """Provide a random, temporary nii file."""
    
    nii = generate_random_nii()
    nii_path = tmp_path / "random.nii"
    nib.save(nii, nii_path)

    return nii_path

    

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
    intensity_normalization(rescaling_method=RESCALING_10000_GLOBALMEDIAN,
                            target_dir=TARGET_DIR_PATH,
                            median_intensity=None,
                            rescaling_factor=None,
                            output_dir=OUTPUT_DIR_PATH,
                            )

@pytest.mark.skip(reason="Not yet implemented")
def test_intensity_normalization_100_voxel_mean():
    intensity_normalization(rescaling_method=RESCALING_100_VOXELMEAN,
                            target_dir=TARGET_DIR_PATH,
                            median_intensity=None,
                            rescaling_factor=None,
                            output_dir=OUTPUT_DIR_PATH,
                            )

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