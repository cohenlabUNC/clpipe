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

NUM_FMRIPREP_SUBJECTS = 8

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

#TODO: seperate AROMA into its own type of fmriprep dir
@pytest.fixture(scope="session")
def clpipe_fmriprep_dir(tmp_path_factory, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, sample_melodic_mixing, sample_aroma_noise_ics, 
    sample_fmriprep_dataset_description) -> Path:
    """ Fixture which adds fmriprep subject folders and mock 
    fmriprep output data to data_fmriprep directory of clpipe project.
    """

    tasks = ["rest", "1", "2_run-1", "2_run-2"]

    image_space = "space-MNI152NLin2009cAsym"
    bold_suffix = "desc-preproc_bold.nii.gz"
    mask_suffix = "desc-brain_mask.nii.gz"
    sidecar_suffix = "desc-preproc_bold.json"
    confounds_suffix = "desc-confounds_timeseries.tsv"
    melodic_mixing_suffix = "desc-MELODIC_mixing.tsv"
    aroma_noise_ics_suffix = "AROMAnoiseICs.csv"

    project_dir = tmp_path_factory.mktemp("clpipe_fmriprep_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))

    fmriprep_dir = project_dir / "data_fmriprep" / "fmriprep"
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

    return project_dir

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



@pytest.fixture(scope="session")
def config_file(clpipe_dir):
    return clpipe_dir / "clpipe_config.json"

@pytest.fixture(scope="session")
def config_file_fmriprep(clpipe_fmriprep_dir: Path):
    """Return config file from the test fmriprep directory."""

    return clpipe_fmriprep_dir / "clpipe_config.json"

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

@pytest.fixture(scope="session")
def clpipe_config(config_file) -> dict:
    with open(config_file, 'r') as f:
        config_dict = json.load(f)
        return config_dict

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
def clpipe_dir_old_glm_config(tmp_path_factory):
    """Fixture which provides a temporary clpipe project folder."""
    
    # TODO: change how tests work such that clpipe directory populating works as functions not fixtures

    PROJECT_TITLE = "old_glm_setup"
    project_dir = tmp_path_factory.mktemp(PROJECT_TITLE)

    # Monkeypatch setup_glm to use the old method
    ClpipeConfigParser.setup_glm = _old_setup_glm

    GLMConfigParser.__init__ = _old_setup_glm_init

    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))

    return project_dir


def _old_setup_glm_init(self, glm_config_file=None):
        import json
        from pkg_resources import resource_stream
        from clpipe.config_json_parser import config_json_parser

        if glm_config_file is None:
            with resource_stream(__name__, '/data/old_GLMConfig.json') as def_config:
                self.config = json.load(def_config)
        else:
            self.config = config_json_parser(glm_config_file)


def _old_setup_glm(self, project_path):
    """Runs glm setup according to <= v1.7.3"""
    import os
    
    glm_config = GLMConfigParser()

    glm_config.config['GLMSetupOptions']['ParentClpipeConfig'] = os.path.join(project_path, "clpipe_config.json")
    glm_config.config['GLMSetupOptions']['TargetDirectory'] = os.path.join(project_path, "data_fmriprep", "fmriprep")
    glm_config.config['GLMSetupOptions']['MaskFolderRoot'] = glm_config.config['GLMSetupOptions']['TargetDirectory']
    glm_config.config['GLMSetupOptions']['PreppedDataDirectory'] =  os.path.join(project_path, "data_GLMPrep")

    glm_config.config['Level1Setups'][0]['TargetDirectory'] = os.path.join(project_path, "data_GLMPrep")
    glm_config.config['Level1Setups'][0]['FSFDir'] = os.path.join(project_path, "l1_fsfs")
    glm_config.config['Level1Setups'][0]['EVDirectory'] = os.path.join(project_path, "data_onsets")
    glm_config.config['Level1Setups'][0]['ConfoundDirectory'] = os.path.join(project_path, "data_GLMPrep")
    glm_config.config['Level1Setups'][0]['OutputDir'] = os.path.join(project_path, "l1_feat_folders")

    glm_config.config['Level2Setups'][0]['OutputDir'] = os.path.join(project_path, "l2_gfeat_folders")
    glm_config.config['Level2Setups'][0]['OutputDir'] = os.path.join(project_path, "l2_fsfs")

    glm_config.config['GLMSetupOptions']['LogDirectory'] = os.path.join(project_path, "logs", "glm_setup_logs")

    glm_config.config_json_dump(project_path, "glm_config.json")