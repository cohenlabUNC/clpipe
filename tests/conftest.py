import pytest
import sys
import shutil
import json
from pathlib import Path
from bids import BIDSLayout, BIDSLayoutIndexer
from clpipe.bids import get_bids


import nibabel as nib
import nipype.pipeline.engine as pe
from nilearn import plotting
from nilearn.image import load_img, index_img

sys.path.append("../clpipe")
from clpipe.project_setup import project_setup
from clpipe.config_json_parser import ClpipeConfigParser, GLMConfigParser
from clpipe.config.options import convert_project_options
import utils

PROJECT_TITLE = "test_project"
LEGACY_CONFIG_PATH = "tests/data/legacy_config.json"

#################
# Option Config #
#################


def pytest_addoption(parser):
    """Adds addtional options to pytest when running clpipe tests."""

    parser.addoption(
        "--plot_img",
        action="store_true",
        default=False,
        help="Save plot of image processing results as .png",
    )
    parser.addoption(
        "--write_graph",
        action="store",
        default=False,
        help="Save plot of image processing results as .png",
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
    the helpers fixtures."""

    @staticmethod
    def plot_4D_img_slice(image_path: Path, png_name: str):
        image = load_img(str(image_path))
        image_slice = index_img(image, 1)

        plot_path = image_path.parent / png_name
        plotting.plot_img(image_slice, output_file=plot_path)

    @staticmethod
    def plot_timeseries(
        image_path: Path,
        base_image_path: Path,
        highlight_ranges: list = None,
        num_figs: int = 4,
    ):
        import nibabel as nib
        import numpy as np
        import matplotlib.pyplot as plt

        image = nib.load(str(image_path))
        base_image = nib.load(str(base_image_path))

        data = image.get_fdata()
        n_timepoints, n_voxels = data.shape[-1], np.prod(data.shape[:-1])

        base_data = base_image.get_fdata()
        base_n_timepoints, base_n_voxels = base_data.shape[-1], np.prod(
            base_data.shape[:-1]
        )

        # Place all voxels on one axis
        data_2d = np.reshape(data, (n_voxels, n_timepoints))
        base_data_2d = np.reshape(base_data, (base_n_voxels, base_n_timepoints))

        import math

        if num_figs > 4 or num_figs < 1:
            raise ValueError("num_figs must be in the range 1-4")

        # TODO: Abstract this logic.
        nrows = 1
        ncols = 1
        if num_figs == 2:
            ncols = 2
        elif num_figs == 3:
            ncols = 3
        elif num_figs == 4:
            nrows = 2
            ncols = 2

        fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(12, 8))
        if num_figs == 1:
            axs = [axs]
        else:
            axs = axs.flatten()
        axes_to_show = [95806, 84147, 77717, 86717]
        axes_to_show = axes_to_show[:num_figs]
        fig.supxlabel("Time")
        fig.supylabel("Signal intensity")

        for i, ax in enumerate(axs):
            data = data_2d[axes_to_show[i]]
            base_data = base_data_2d[axes_to_show[i]]

            # Select a random voxel to plot
            # Plot the time-series data
            (processed_plot,) = ax.plot(data, label="processed")
            (raw_plot,) = ax.plot(base_data, label="raw")
            ax.set_title(f"voxel: {axes_to_show[i]}")

            # Set the x-axis ticks to display all integers
            axis_len = len(data)
            axis_range = range(0, axis_len)
            ticklabels = [str(tick) if tick % 10 == 0 else "" for tick in axis_range]
            ax.set_xticks(axis_range)
            ax.set_xticklabels(ticklabels)
            # ax.set_xlim(1, axis_len)

            if highlight_ranges:
                for highlight_range in highlight_ranges:
                    ax.axvspan(
                        highlight_range[0], highlight_range[1], color="red", alpha=0.2
                    )

        fig.legend(handles=[raw_plot, processed_plot])

        save_path = image_path.parent / "timeseries.png"
        plt.savefig(save_path)

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

    The image consists of slices 100-110 of
        sub-09113/func/sub-09113_task-heart_bold.nii.gz

    Useful for tests that require a shorter timeseries for runtime consideration,
    or those where timeseries length is not important.
    """

    return Path("tests/data/sample_raw.nii.gz").resolve()


@pytest.fixture(scope="session")
def sample_raw_image_longer() -> Path:
    """
    Based on same image as sample_raw_image but uses 100 timepoints, from 100-200.

    Useful for tests that require more timepoints.
    """

    return Path("tests/data/sample_raw_longer.nii.gz").resolve()


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
    return Path("tests/data/sample_postprocessed_confounds.tsv").resolve()


@pytest.fixture(scope="session")
def sample_nuisance_file() -> Path:
    with open("tests/data/sample_nuisance_file.txt", "w") as f:
        f.write("0\n0\n1\n0\n0\n0\n1\n0\n0\n0")
    return Path("tests/data/sample_nuisance_file.txt").resolve()


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
    return Path(
        "tests/artifacts/tpl-MNIPediatricAsym_cohort-2_res-1_T1w.nii.gz"
    ).resolve()


@pytest.fixture(scope="session")
def source_data(tmp_path_factory):
    """Fixture which provides a temporary space for a source data folder."""
    source_path = tmp_path_factory.mktemp("source_data")
    return Path(source_path)


########################
# Project Dir Fixtures #
########################


@pytest.fixture(scope="function")
def scatch_dir(tmp_path_factory):
    """Fixture which provides a temporary folder."""

    scratch_dir = tmp_path_factory.mktemp("scratch")
    return scratch_dir


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
def clpipe_bids_dir(tmp_path_factory, sample_raw_image):
    """Fixture provides a clpipe project with mock BIDS folders."""

    project_dir = tmp_path_factory.mktemp("clpipe_bids_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))
    utils.populate_with_BIDS(project_dir, sample_raw_image)

    return project_dir


@pytest.fixture(scope="session")
def clpipe_postproc_dir(
    tmp_path_factory,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    sample_fmriprep_dataset_description,
) -> Path:
    """Fixture which adds postproc subject folders and mock
    postproc output data to data_postproc directory of clpipe project.
    """
    project_dir = tmp_path_factory.mktemp("clpipe_bids_fmriprep_postproc_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))

    utils.populate_with_BIDS(project_dir, sample_raw_image)
    utils.populate_with_fmriprep(
        project_dir,
        sample_raw_image,
        sample_raw_image_mask,
        sample_confounds_timeseries,
        sample_melodic_mixing,
        sample_aroma_noise_ics,
        sample_fmriprep_dataset_description,
        legacy=False,
    )
    utils.populate_with_postproc(
        project_dir, sample_raw_image, sample_confounds_timeseries
    )

    return project_dir


@pytest.fixture(scope="session")
def clpipe_postproc_legacy_fmriprep_dir(
    tmp_path_factory,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    sample_fmriprep_dataset_description,
) -> Path:
    """Same as clpipe_postproc_dir but uses legacy fmriprep.
    Ideally that function would be parameterized with legacy=True/False,
        but have not figured out how to do this with fixtures yet #TODO
    """
    project_dir = tmp_path_factory.mktemp("clpipe_bids_fmriprep_postproc_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))

    utils.populate_with_BIDS(project_dir, sample_raw_image)
    utils.populate_with_fmriprep(
        project_dir,
        sample_raw_image,
        sample_raw_image_mask,
        sample_confounds_timeseries,
        sample_melodic_mixing,
        sample_aroma_noise_ics,
        sample_fmriprep_dataset_description,
        legacy=True,
    )
    utils.populate_with_postproc(
        project_dir, sample_raw_image, sample_confounds_timeseries
    )

    return project_dir


# TODO: seperate AROMA into its own type of fmriprep dir
@pytest.fixture(scope="session")
def clpipe_fmriprep_dir(
    tmp_path_factory,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    sample_fmriprep_dataset_description,
) -> Path:
    """Fixture which adds fmriprep subject folders and mock
    fmriprep output data to data_fmriprep directory of clpipe project.
    """
    project_dir = tmp_path_factory.mktemp("clpipe_bids_fmriprep_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))

    utils.populate_with_BIDS(project_dir, sample_raw_image)
    utils.populate_with_fmriprep(
        project_dir,
        sample_raw_image,
        sample_raw_image_mask,
        sample_confounds_timeseries,
        sample_melodic_mixing,
        sample_aroma_noise_ics,
        sample_fmriprep_dataset_description,
        legacy=False,
    )

    return project_dir


@pytest.fixture(scope="session")
def clpipe_postprocess_subjects(clpipe_fmriprep_dir: Path):
    """Runs postprocess_subjects on fmriprep fixtures,
    generating the first step of postprocess outputs, including a run_config.json."""

    from clpipe.config.options import ProjectOptions
    from clpipe.postprocess import postprocess_subjects

    config = clpipe_fmriprep_dir / "clpipe_config.json"

    options = ProjectOptions.load(config)
    options.postprocessing.working_directory = clpipe_fmriprep_dir / "data_working"

    postprocess_subjects(config_file=options)

    return clpipe_fmriprep_dir


@pytest.fixture(scope="session")
def clpipe_fmriprep_indexed_dir(clpipe_fmriprep_dir) -> Path:
    project_dir = clpipe_fmriprep_dir
    get_bids(
        project_dir / "data_BIDS",
        database_path=project_dir / "BIDS_index",
        index_metadata=True,
        fmriprep_dir=project_dir / "data_fmriprep",
    )
    return project_dir


# TODO: seperate AROMA into its own type of fmriprep dir
@pytest.fixture(scope="session")
def clpipe_legacy_fmriprep_dir(
    tmp_path_factory,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    sample_fmriprep_dataset_description,
) -> Path:
    """Fixture which adds fmriprep subject folders and mock
    fmriprep output data to data_fmriprep directory of clpipe project.
    """
    project_dir = tmp_path_factory.mktemp("clpipe_bids_legacy_fmriprep_dir")
    project_setup(project_title=PROJECT_TITLE, project_dir=str(project_dir))

    utils.populate_with_BIDS(project_dir, sample_raw_image)
    utils.populate_with_fmriprep(
        project_dir,
        sample_raw_image,
        sample_raw_image_mask,
        sample_confounds_timeseries,
        sample_melodic_mixing,
        sample_aroma_noise_ics,
        sample_fmriprep_dataset_description,
        legacy=True,
    )

    return project_dir


##################################
# Project Configuration Fixtures #
##################################


@pytest.fixture(scope="session")
def config_file(clpipe_dir):
    return clpipe_dir / "clpipe_config.json"


@pytest.fixture(scope="session")
def clpipe_config(config_file) -> dict:
    with open(config_file, "r") as f:
        config_dict = json.load(f)
        return config_dict


@pytest.fixture(scope="module")
def clpipe_config_default() -> dict:
    return ClpipeConfigParser().config


@pytest.fixture(scope="module")
def legacy_config_path() -> Path:
    return Path(LEGACY_CONFIG_PATH)


@pytest.fixture(scope="function")
def legacy_config_dir(tmp_path_factory) -> Path:
    """A dir simply for holding a legacy config file for testing."""
    temp_dir = tmp_path_factory.mktemp("legacy_config_dir")

    temp_config_file = temp_dir / "clpipe_config.json"

    import shutil

    shutil.copy(LEGACY_CONFIG_PATH, temp_config_file)

    return temp_dir


@pytest.fixture(scope="session")
def project_config(clpipe_config):
    """Provide the project config as populated by default config file."""

    return convert_project_options(clpipe_config)


@pytest.fixture(scope="session")
def postproc_config(project_config):
    """Provide the project config as populated by default config file."""
    return project_config.postprocess_config


@pytest.fixture(scope="module")
def postprocessing_config(clpipe_config_default):
    return clpipe_config_default["PostProcessingOptions"]


@pytest.fixture(scope="session")
def config_file_confounds(clpipe_config_default, config_file):
    clpipe_config_default["PostProcessingOptions"]["ConfoundOptions"]["Include"] = True

    with open(config_file, "w") as f:
        json.dump(clpipe_config_default, f)

    return config_file


@pytest.fixture(scope="session")
def config_file_aroma(clpipe_config_default, config_file):
    clpipe_config_default["PostProcessingOptions"]["ProcessingSteps"] = [
        "AROMARegression",
        "SpatialSmoothing",
        "IntensityNormalization",
    ]

    with open(config_file, "w") as f:
        json.dump(clpipe_config_default, f)

    return config_file


@pytest.fixture(scope="session")
def config_file_aroma_confounds(clpipe_config_default, config_file):
    clpipe_config_default["PostProcessingOptions"]["ConfoundOptions"]["Include"] = True
    clpipe_config_default["PostProcessingOptions"]["ProcessingSteps"] = [
        "AROMARegression",
        "TemporalFiltering",
    ]

    with open(config_file, "w") as f:
        json.dump(clpipe_config_default, f)

    return config_file


@pytest.fixture(scope="session")
def config_file_fmriprep(clpipe_fmriprep_dir: Path):
    """Return config file from the test fmriprep directory."""

    return clpipe_fmriprep_dir / "clpipe_config.json"


@pytest.fixture(scope="module")
def config_file_postproc(clpipe_postproc_dir: Path):
    """Return config file from the test postproc directory."""

    return clpipe_postproc_dir / "clpipe_config.json"


@pytest.fixture(scope="module")
def config_file_postproc_legacy_fmriprep(clpipe_postproc_legacy_fmriprep_dir: Path):
    """Same as config_file_postproc but with legacy fmriprep dir."""

    return clpipe_postproc_legacy_fmriprep_dir / "clpipe_config.json"


@pytest.fixture(scope="session")
def config_file_legacy_fmriprep(clpipe_legacy_fmriprep_dir: Path):
    return clpipe_legacy_fmriprep_dir / "clpipe_config.json"


@pytest.fixture(scope="module")
def glm_config_default():
    """Returns the default glm config file."""
    return GLMConfigParser().config


@pytest.fixture(scope="session")
def glm_config_file(clpipe_fmriprep_dir: Path) -> Path:
    """Provides a reference to a glm_config.json file that
    has been setup in the context of a mock project.
    """
    return clpipe_fmriprep_dir / "glm_config.json"


@pytest.fixture(scope="session")
def old_glm_config_file(clpipe_dir_old_glm_config: Path) -> Path:
    """Returns a reference to an old-style glm config populated with project setup."""
    return clpipe_dir_old_glm_config / "glm_config.json"


#####################
# Workflow Fixtures #
#####################


@pytest.fixture(scope="function")
def workflow_base(tmp_path):
    """Returns a minimal nypipe workflow."""

    wf = pe.Workflow(name="Test_Workflow", base_dir=tmp_path)
    wf.config["execution"]["crashdump_dir"] = "nypipe_crashdumps"
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
