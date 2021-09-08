import sys
import pytest
sys.path.append('../clpipe')

from click.testing import CliRunner
from pathlib import Path

from clpipe.intensity_normalization import *

#tmpdir = setup_test_directory(temporary=True, populate_fmriprep=True)

CONFIG_FILE_PATH = "clpipe_config.json"
TARGET_DIR_PATH = "data_fmriprep"
OUTPUT_DIR_PATH = "data_postproc/postproc_normalize"
OUTPUT_SUFFIX = "_normalized"
LOG_DIR_PATH = "logs"

logging.basicConfig(level=logging.INFO)

PROJECT_TITLE = "test_project"
from click.testing import CliRunner
from clpipe.project_setup import project_setup

@pytest.fixture
def clpipe_dir(tmpdir):
    #TODO: abstract this out for use in future test modules
    """Fixture which provides a temporary clpipe project folder."""
    raw_data = Path(tmpdir / "data_DICOMs")
    raw_data.mkdir(parents=True, exist_ok=True)

    # Use the clpipe CLI to setup project
    runner = CliRunner()
    result = runner.invoke(
        project_setup, 
        [
            '-project_title', PROJECT_TITLE, 
            '-project_dir', str(tmpdir),
            '-source_data', str(raw_data), 
        ]
    )

    # Raise any exceptions from the CLI
    if result.exit_code != 0:
        raise Exception(result.exception)

    return tmpdir


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

def test_calculate_100_voxel_mean(clpipe_dir):
    image = None
    calculate_100_voxel_mean(str(clpipe_dir), str(clpipe_dir))

if __name__ == "__main__":
    test_calculate_100_voxel_mean()