import sys
import pytest
from pathlib import Path

from click.testing import CliRunner

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

logging.basicConfig(level=logging.INFO)

@pytest.fixture(scope="session")
def clpipe_dir(tmpdir_factory):
    #TODO: abstract this out for use in future test modules
    """Fixture which provides a temporary clpipe project folder."""
    proj_path = tmpdir_factory.mktemp(PROJECT_TITLE)
    
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

@pytest.mark.skip(reason="Not yet implemented")
def test_calculate_10000_global_median():
    image = None
    calculate_10000_global_median(image)

def test_calculate_100_voxel_mean(clpipe_fmriprep_dir):
    image = None
    calculate_100_voxel_mean(str(clpipe_fmriprep_dir), str(clpipe_fmriprep_dir))

if __name__ == "__main__":
    test_calculate_100_voxel_mean()