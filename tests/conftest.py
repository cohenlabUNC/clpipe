import pytest
import sys
import shutil
import json
from pathlib import Path

import nibabel as nib
import nipype.pipeline.engine as pe
from nilearn import plotting
from nilearn.image import load_img, index_img

sys.path.append('../clpipe')
from clpipe.project_setup import project_setup
from clpipe.config_json_parser import ClpipeConfigParser, GLMConfigParser
import utils

PROJECT_TITLE = "test_project"

#################
# Option Config #
#################

def pytest_addoption(parser):
    """Adds addtional options to pytest when running clpipe tests."""

    parser.addoption(
        "--plot_img", action="store_true", default=False, help="Save plot of image processing results as .png"
    )
    parser.addoption(
        "--write_graph", action="store", default=False, help="Save plot of image processing results as .png"
    )

@pytest.fixture(scope="package")
def plot_img(request):
    """Makes the value of custom flag available as fixture to tests."""
    return request.config.getoption("--plot_img")

@pytest.fixture(scope="package")
def write_graph(request):
    """Makes the value of custom flag available as fixture to tests."""
    return request.config.getoption("--write_graph")

##########################
# Helper Function Config #
##########################

class Helpers:
    """Functions in this class are made available to all tests as a fixtures via
    the helpers fixtures. """

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
    
@pytest.fixture(scope="package")
def helpers():
    """Provide the helper class functions as fixture usable by tests."""
    return Helpers

#####################
# Resource Fixtures #
#####################

@pytest.fixture(scope="package")
def artifact_dir():
    """Provides a path for storing persistent test artifacts.
    Some tests produce image outputs that may need to be inspected later,
    thus not being suited for placing in a temporary folder.
    """
    return Path("tests", "artifacts").resolve()

@pytest.fixture(scope="session")
def sample_raw_image() -> Path:
    """
    This is image is from the OpenNeuro dataset:
    'Interoception during aging: The heartbeat detection task'
    Located at https://openneuro.org/datasets/ds003763/versions/1.0.0

    The image consists of slices 100-110 of sub-09113/func/sub-09113_task-heart_bold.nii.gz
    """
    
    return Path("tests/data/sample_raw.nii.gz").resolve()

@pytest.fixture(scope="session")
def sample_raw_image_mask() -> Path:
    """
    This image is a mask of the sample_raw_image fixture.

    The mask was calculated with nilearn's masking.compute_epi_mask function.
    """
    
    return Path("tests/data/sample_raw_mask.nii.gz").resolve()

@pytest.fixture(scope="session")
def sample_confounds_timeseries() -> Path:
    return Path("tests/data/sample_confounds_timeseries.tsv").resolve()

@pytest.fixture(scope="session")
def sample_postprocessed_confounds() -> Path:
    return Path("tests/data/postprocessed_confounds.tsv").resolve()

@pytest.fixture(scope="session")
def sample_melodic_mixing() -> Path:
    return Path("tests/data/MELODIC_mixing.tsv").resolve()

@pytest.fixture(scope="session")
def sample_aroma_noise_ics() -> Path:
    return Path("tests/data/AROMAnoiseICs.csv").resolve()

@pytest.fixture(scope="session")
def sample_fmriprep_dataset_description() -> Path:
    return Path("tests/data/dataset_description.json").resolve()

@pytest.fixture(scope="session")
def sample_reference() -> Path:
    return Path("tests/artifacts/tpl-MNIPediatricAsym_cohort-2_res-1_T1w.nii.gz").resolve()

@pytest.fixture(scope="session")
def source_data(tmp_path_factory):
    """Fixture which provides a temporary space for a source data folder."""
    source_path = tmp_path_factory.mktemp("source_data")
    return Path(source_path)

########################
# Project Dir Fixtures #
########################

@pytest.fixture(scope="session")
def clpipe_dir(tmp_path_factory):
    """Fixture which provides a temporary clpipe project folder."""
    
    project_dir = tmp_path_factory.mktemp("clpipe_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))
    
    return project_dir

@pytest.fixture(scope="session")
def clpipe_dicom_dir(tmp_path_factory):
    """Fixture which provides a clpipe project with different varieties of DICOM folder structures"""

    project_dir = tmp_path_factory.mktemp("clpipe_dicom_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))
    utils.populate_with_DICOM(project_dir)

    return project_dir

@pytest.fixture(scope="session")
def clpipe_bids_dir(tmp_path_factory):
    """Fixture provides a clpipe project with mock BIDS folders."""

    project_dir = tmp_path_factory.mktemp("clpipe_bids_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))
    utils.populate_with_BIDS(project_dir)

    return clpipe_dir

@pytest.fixture(scope="session")
def clpipe_postproc2_dir(tmp_path_factory, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
    sample_fmriprep_dataset_description) -> Path:
    """ Fixture which adds postproc2 subject folders and mock 
    postproc2 output data to data_postproc2 directory of clpipe project.
    """
    project_dir = tmp_path_factory.mktemp("clpipe_bids_fmriprep_postproc2_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))
    
    utils.populate_with_BIDS(project_dir, sample_raw_image)
    utils.populate_with_fmriprep(project_dir, sample_raw_image, sample_raw_image_mask, 
        sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
        sample_fmriprep_dataset_description, legacy = False)
    utils.populate_with_postproc2(project_dir, sample_raw_image,  sample_confounds_timeseries)

    return project_dir

#TODO: seperate AROMA into its own type of fmriprep dir
@pytest.fixture(scope="session")
def clpipe_fmriprep_dir(tmp_path_factory, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
    sample_fmriprep_dataset_description) -> Path:
    """ Fixture which adds fmriprep subject folders and mock 
    fmriprep output data to data_fmriprep directory of clpipe project.
    """
    project_dir = tmp_path_factory.mktemp("clpipe_bids_fmriprep_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))

    utils.populate_with_BIDS(project_dir, sample_raw_image)
    utils.populate_with_fmriprep(project_dir, sample_raw_image, sample_raw_image_mask, 
        sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
        sample_fmriprep_dataset_description, legacy = False)

    return project_dir

#TODO: seperate AROMA into its own type of fmriprep dir
@pytest.fixture(scope="session")
def clpipe_legacy_fmriprep_dir(tmp_path_factory, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
    sample_fmriprep_dataset_description) -> Path:
    """ Fixture which adds fmriprep subject folders and mock 
    fmriprep output data to data_fmriprep directory of clpipe project.
    """
    project_dir = tmp_path_factory.mktemp("clpipe_bids_legacy_fmriprep_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))

    utils.populate_with_BIDS(project_dir, sample_raw_image)
    utils.populate_with_fmriprep(project_dir, sample_raw_image, sample_raw_image_mask, 
        sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
        sample_fmriprep_dataset_description, legacy = True)

    return project_dir

@pytest.fixture(scope="session")
def clpipe_dir_old_glm_config(tmp_path_factory, sample_raw_image, sample_raw_image_mask, 
        sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
        sample_fmriprep_dataset_description):
    """Fixture which provides a project using the old glm config."""

    project_dir = tmp_path_factory.mktemp("clpipe_old_glm_dir")

    # Monkeypatch setup_glm to use the old method
    ClpipeConfigParser.setup_glm = utils.old_setup_glm

    GLMConfigParser.__init__ = utils.old_GLMConfigParser_init

    project_setup(project_title=PROJECT_TITLE, project_dir=project_dir)
    utils.populate_with_BIDS(project_dir)
    utils.populate_with_fmriprep(project_dir, sample_raw_image, sample_raw_image_mask, 
        sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
        sample_fmriprep_dataset_description)

    return project_dir

##################################
# Project Configuration Fixtures #
##################################

@pytest.fixture(scope="session")
def config_file(clpipe_dir):
    return clpipe_dir / "clpipe_config.json"

@pytest.fixture(scope="session")
def clpipe_config(config_file) -> dict:
    with open(config_file, 'r') as f:
        config_dict = json.load(f)
        return config_dict

@pytest.fixture(scope="module")
def clpipe_config_default() -> dict:
    return ClpipeConfigParser().config

@pytest.fixture(scope="module")
def postprocessing_config(clpipe_config_default):
    return clpipe_config_default["PostProcessingOptions2"]

@pytest.fixture(scope="session")
def config_file_confounds(clpipe_config_default, config_file):
    clpipe_config_default["PostProcessingOptions2"]["ConfoundOptions"]["Include"] = True

    with open(config_file, 'w') as f:
        json.dump(clpipe_config_default, f)

    return config_file

@pytest.fixture(scope="session")
def config_file_aroma(clpipe_config_default, config_file):
    clpipe_config_default["PostProcessingOptions2"]["ProcessingSteps"] = ["AROMARegression", "SpatialSmoothing", "IntensityNormalization"]

    with open(config_file, 'w') as f:
        json.dump(clpipe_config_default, f)

    return config_file

@pytest.fixture(scope="session")
def config_file_aroma_confounds(clpipe_config_default, config_file):
    clpipe_config_default["PostProcessingOptions2"]["ConfoundOptions"]["Include"] = True
    clpipe_config_default["PostProcessingOptions2"]["ProcessingSteps"] = ["AROMARegression", "TemporalFiltering"]

    with open(config_file, 'w') as f:
        json.dump(clpipe_config_default, f)

    return config_file

@pytest.fixture(scope="session")
def config_file_fmriprep(clpipe_fmriprep_dir: Path):
    """Return config file from the test fmriprep directory."""

    return clpipe_fmriprep_dir / "clpipe_config.json"

@pytest.fixture(scope="module")
def glm_config_default():
    """Returns the default glm config file."""
    return GLMConfigParser().config

@pytest.fixture(scope="session")
def glm_config_file(clpipe_fmriprep_dir: Path) -> Path:
    """Provides a reference to a glm_config.json file that
    has been setup in the context of a mock project.

    Args:
        clpipe_fmriprep_dir (Path): Path to a mock fmriprep clpipe project

    Returns:
        Path: Reference to mock glm_config.json file.
    """
    return clpipe_fmriprep_dir / "glm_config.json"

#####################
# Workflow Fixtures #
#####################

@pytest.fixture(scope="function")
def workflow_base(tmp_path):
    """Returns a minimal nypipe workflow. """

    wf =  pe.Workflow(name="Test_Workflow", base_dir=tmp_path)
    wf.config['execution']['crashdump_dir'] = "nypipe_crashdumps"
    return wf

######################
# Generated Fixtures #
######################

@pytest.fixture
def random_nii(tmp_path) -> Path:
    """Save a random, temporary nii file and provide the path."""
    
    nii = utils.generate_random_nii()
    nii_path = tmp_path / "random.nii"
  
    nib.save(nii, nii_path)
    return nii_path

@pytest.fixture
def random_nii_mask(tmp_path) -> Path:
    """Save a random, temporary nii mask file and provide the path."""

    nii = utils.generate_random_nii_mask()
    nii_path = tmp_path / "random_mask.nii"

    nib.save(nii, nii_path)
    return nii_path