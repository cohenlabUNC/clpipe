import pytest
import sys
import shutil
import json
from pathlib import Path

import numpy as np
import nibabel as nib
import nipype.pipeline.engine as pe
from nilearn import plotting
from nilearn.image import load_img, index_img

from click.testing import CliRunner

sys.path.append('../clpipe')
from clpipe.project_setup import project_setup
from clpipe.config_json_parser import ClpipeConfigParser, GLMConfigParser

PROJECT_TITLE = "test_project"
NUM_BIDS_SUBJECTS = 10
NUM_DICOM_SUBJECTS = 5
DICOM_SESSIONS = ['2000', '2010', '2020']
NUM_FMRIPREP_SUBJECTS = 8
DEFAULT_RANDOM_NII_DIMS = (12, 12, 12, 36)

class Helpers:
    @staticmethod
    def plot_4D_img_slice(image_path: Path, png_name: str):
        image = load_img(str(image_path))
        image_slice = index_img(image, 1)
    
        plot_path = image_path.parent / png_name
        plotting.plot_img(image_slice, output_file=plot_path)

    @staticmethod
    def create_test_dir(artifact_dir: Path, name: str):
        test_path = artifact_dir / name
        test_path.mkdir(parents=True, exist_ok=True)

        return test_path

def pytest_addoption(parser):
    parser.addoption(
        "--plot_img", action="store_true", default=False, help="Save plot of image processing results as .png"
    )
    parser.addoption(
        "--write_graph", action="store", default=False, help="Save plot of image processing results as .png"
    )

@pytest.fixture(scope="package")
def helpers():
    return Helpers

@pytest.fixture(scope="package")
def plot_img(request):
    return request.config.getoption("--plot_img")

@pytest.fixture(scope="package")
def write_graph(request):
    return request.config.getoption("--write_graph")

@pytest.fixture(scope="package")
def artifact_dir():
    return Path("tests", "artifacts").resolve()

@pytest.fixture(scope="package")
def sample_raw_image() -> Path:
    """
    This is image is from the OpenNeuro dataset:
    'Interoception during aging: The heartbeat detection task'
    Located at https://openneuro.org/datasets/ds003763/versions/1.0.0

    The image consists of slices 100-110 of sub-09113/func/sub-09113_task-heart_bold.nii.gz
    """
    
    return Path("tests/data/sample_raw.nii.gz").resolve()

@pytest.fixture(scope="package")
def sample_raw_image_mask() -> Path:
    """
    This image is a mask of the sample_raw_image fixture.

    The mask was calculated with nilearn's masking.compute_epi_mask function.
    """
    
    return Path("tests/data/sample_raw_mask.nii.gz").resolve()


@pytest.fixture(scope="function")
def project_dir(tmp_path_factory):
    """Fixture which provides a temporary space for a project folder."""
    proj_path = tmp_path_factory.mktemp(PROJECT_TITLE)
    return Path(proj_path)

@pytest.fixture(scope="function")
def source_data(tmp_path_factory):
    """Fixture which provides a temporary space for a source data folder."""
    source_path = tmp_path_factory.mktemp("source_data")
    return Path(source_path)


@pytest.fixture(scope="module")
def clpipe_dir(tmp_path_factory):
    """Fixture which provides a temporary clpipe project folder."""
    
    project_dir = tmp_path_factory.mktemp(PROJECT_TITLE)

    raw_data = Path(project_dir / "data_DICOMs")
    raw_data.mkdir(parents=True, exist_ok=True)

    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir),
        source_data=str(raw_data))

    return project_dir

@pytest.fixture(scope="module")
def clpipe_dicom_dir(clpipe_dir):
    """Fixture which adds different varieties of DICOM folder structures"""

    dicom_dir = clpipe_dir / "data_DICOMs"

    sub = dicom_dir / "sub"
    session_sub = dicom_dir / "session_sub"
    session_sub_flat = dicom_dir / "session_sub_flat"
    sub_session = dicom_dir / "sub_session"
    sub_session_flat = dicom_dir / "sub_session_flat"

    for sub_num in range(NUM_DICOM_SUBJECTS):
        sub_folder = sub / str(sub_num)
        sub_folder.mkdir(parents=True, exist_ok=True)

        for session in DICOM_SESSIONS:
            sub_session_folder = sub_session / str(sub_num) / session
            sub_session_folder.mkdir(parents=True, exist_ok=True)

            sub_session_folder_flat = sub_session_flat / Path(str(sub_num) + "_" + session)
            sub_session_folder_flat.mkdir(parents=True, exist_ok=True)

            session_sub_folder = session_sub / session / str(sub_num)
            session_sub_folder.mkdir(parents=True, exist_ok=True)

            session_sub_folder_flat = session_sub_flat / Path(session + "_" + str(sub_num))
            session_sub_folder_flat.mkdir(parents=True, exist_ok=True)

            

    return dicom_dir


@pytest.fixture(scope="module")
def clpipe_bids_dir(clpipe_dir):
    """Fixture which adds some subject folders to data_BIDS."""

    for sub_num in range(NUM_BIDS_SUBJECTS):
            subject_folder = clpipe_dir / "data_BIDS" / f"sub-{sub_num}"
            subject_folder.mkdir()

    return clpipe_dir

#TODO: seperate AROMA into its own type of fmriprep dir
@pytest.fixture(scope="module")
def clpipe_fmriprep_dir(clpipe_bids_dir, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
    sample_fmriprep_dataset_description) -> Path:
    """ Fixture which adds fmriprep subject folders and mock 
    fmriprep output data to data_fmriprep directory.
    """

    tasks = ["rest", "1", "2_run-1", "2_run-2"]

    image_space = "space-MNI152NLin2009cAsym"
    bold_suffix = "desc-preproc_bold.nii.gz"
    mask_suffix = "desc-brain_mask.nii.gz"
    sidecar_suffix = "desc-preproc_bold.json"
    confounds_suffix = "desc-confounds_timeseries.tsv"
    melodic_mixing_suffix = "desc-MELODIC_mixing.tsv"
    aroma_noise_ics_suffix = "AROMAnoiseICs.csv"

    fmriprep_dir = clpipe_bids_dir / "data_fmriprep" / "fmriprep"
    fmriprep_dir.mkdir(parents=True)

    shutil.copy(sample_fmriprep_dataset_description, fmriprep_dir)

    for sub_num in range(NUM_FMRIPREP_SUBJECTS):
        subject_folder = fmriprep_dir / f"sub-{sub_num}" / "func"
        subject_folder.mkdir(parents=True)
        

        for task in tasks:
            task_info = f"task-{task}"
            
            shutil.copy(sample_raw_image, subject_folder / f"sub-{sub_num}_{task_info}_{image_space}_{bold_suffix}")
            shutil.copy(sample_raw_image_mask, subject_folder / f"sub-{sub_num}_{task_info}_{image_space}_{mask_suffix}")

            shutil.copy(sample_confounds_timeseries, subject_folder / f"sub-{sub_num}_{task_info}_{confounds_suffix}")
            shutil.copy(sample_melodic_mixing, subject_folder / f"sub-{sub_num}_{task_info}_{melodic_mixing_suffix}")
            shutil.copy(sample_aroma_noise_ics, subject_folder / f"sub-{sub_num}_{task_info}_{aroma_noise_ics_suffix}")

            if task == "rest":
                tr = .6
            else:
                tr = .9
            sidecar_json = {"RepetitionTime": tr, "TaskName": task}
            with open(subject_folder / f"sub-{sub_num}_{task_info}_{image_space}_{sidecar_suffix}", "w") as sidecar_file:
                json.dump(sidecar_json, sidecar_file)

    
    return clpipe_bids_dir

@pytest.fixture(scope="module")
def clpipe_config_default() -> dict:
    return ClpipeConfigParser().config

@pytest.fixture(scope="module")
def glm_config_default():
    return GLMConfigParser().config

@pytest.fixture(scope="module")
def postprocessing_config(clpipe_config_default):
    return clpipe_config_default["PostProcessingOptions2"]

@pytest.fixture(scope="function")
def workflow_base(tmp_path):
    wf =  pe.Workflow(name="Test_Workflow", base_dir=tmp_path)
    wf.config['execution']['crashdump_dir'] = "nypipe_crashdumps"
    return wf

def generate_random_nii(dims: tuple=DEFAULT_RANDOM_NII_DIMS, low: int=0, high: int=1000) -> nib.Nifti1Image:
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

def generate_random_nii_mask(dims: tuple=DEFAULT_RANDOM_NII_DIMS) -> nib.Nifti1Image:
    mask_base = np.ones(dims, dtype=np.int16)
    
    # Zero the edges of our mask
    mask_base[0] = 0
    mask_base[-1] = 0
    for x in mask_base:
        x[0] = 0
        x[-1] = 0
        for y in x:
            y[0] = 0
            y[-1] = 0

    affine = np.diag([1 for x in dims])
    image = nib.Nifti1Image(mask_base, affine)

    return image

@pytest.fixture
def random_nii(tmp_path) -> Path:
    """Save a random, temporary nii file and provide the path."""
    
    nii = generate_random_nii()
    nii_path = tmp_path / "random.nii"
  
    nib.save(nii, nii_path)
    return nii_path

@pytest.fixture
def random_nii_mask(tmp_path) -> Path:
    """Save a random, temporary nii mask file and provide the path."""

    nii = generate_random_nii_mask()
    nii_path = tmp_path / "random_mask.nii"

    nib.save(nii, nii_path)
    return nii_path

@pytest.fixture(scope="module")
def sample_confounds_timeseries() -> Path:
    return Path("tests/data/sample_confounds_timeseries.tsv").resolve()

@pytest.fixture(scope="module")
def sample_postprocessed_confounds() -> Path:
    return Path("tests/data/postprocessed_confounds.tsv").resolve()

@pytest.fixture(scope="module")
def sample_melodic_mixing() -> Path:
    return Path("tests/data/MELODIC_mixing.tsv").resolve()

@pytest.fixture(scope="module")
def sample_aroma_noise_ics() -> Path:
    return Path("tests/data/AROMAnoiseICs.csv").resolve()

@pytest.fixture(scope="module")
def sample_fmriprep_dataset_description() -> Path:
    return Path("tests/data/dataset_description.json").resolve()

@pytest.fixture(scope="module")
def sample_reference() -> Path:
    return Path("tests/artifacts/tpl-MNIPediatricAsym_cohort-2_res-1_T1w.nii.gz").resolve()

@pytest.fixture(scope="module")
def config_file(clpipe_dir):
    return clpipe_dir / "clpipe_config.json"

@pytest.fixture(scope="module")
def config_file_fmriprep(clpipe_fmriprep_dir: Path):
    """Return config file from the test fmriprep directory."""

    return clpipe_fmriprep_dir / "clpipe_config.json"

@pytest.fixture(scope="module")
def glm_config_file(clpipe_fmriprep_dir: Path) -> Path:
    """Provides a reference to a glm_config.json file that
    has been setup in the context of a mock project.

    Args:
        clpipe_fmriprep_dir (Path): Path to a mock fmriprep clpipe project

    Returns:
        Path: Reference to mock glm_config.json file.
    """
    return clpipe_fmriprep_dir / "glm_config.json"

@pytest.fixture(scope="module")
def clpipe_config(config_file) -> dict:
    with open(config_file, 'r') as f:
        config_dict = json.load(f)
        return config_dict

@pytest.fixture(scope="module")
def config_file_confounds(clpipe_config_default, config_file):
    clpipe_config_default["PostProcessingOptions2"]["ConfoundOptions"]["Include"] = True

    with open(config_file, 'w') as f:
        json.dump(clpipe_config_default, f)

    return config_file

@pytest.fixture(scope="module")
def config_file_aroma(clpipe_config_default, config_file):
    clpipe_config_default["PostProcessingOptions2"]["ProcessingSteps"] = ["AROMARegression", "SpatialSmoothing", "IntensityNormalization"]

    with open(config_file, 'w') as f:
        json.dump(clpipe_config_default, f)

    return config_file

@pytest.fixture(scope="module")
def config_file_aroma_confounds(clpipe_config_default, config_file):
    clpipe_config_default["PostProcessingOptions2"]["ConfoundOptions"]["Include"] = True
    clpipe_config_default["PostProcessingOptions2"]["ProcessingSteps"] = ["AROMARegression", "TemporalFiltering"]

    with open(config_file, 'w') as f:
        json.dump(clpipe_config_default, f)

    return config_file
