import pytest
import numpy as np
import nibabel as nib
from pathlib import Path
from click.testing import CliRunner

from clpipe.project_setup import project_setup
from clpipe.config_json_parser import ClpipeConfigParser

PROJECT_TITLE = "test_project"
NUM_SUBJECTS = 8
DEFAULT_RANDOM_NII_DIMS = (3, 3, 3, 12)

@pytest.fixture(scope="session")
def clpipe_dir(tmp_path_factory):
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
    """Fixture which adds fmriprep subject folders and mock fmriprep output data to data_fmriprep directory."""

    config = ClpipeConfigParser()
    target_fmriprep_suffix = config.config["PostProcessingOptions"]["TargetSuffix"]

    for sub_num in range(NUM_SUBJECTS):
        subject_folder = clpipe_dir / "data_fmriprep" / "fmriprep" / f"sub-{sub_num}" / "func"
        subject_folder.mkdir(parents=True)

        nii = generate_random_nii()
        nib.save(nii, subject_folder / f"sub-{sub_num}_task-rest_run-1_{target_fmriprep_suffix}")
    
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