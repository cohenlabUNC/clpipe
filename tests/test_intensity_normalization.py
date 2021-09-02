import sys
sys.path.append('../clpipe')

from click.testing import CliRunner
from pathlib import Path

from clpipe.intensity_normalization import *
from testing_tools import setup_test_directory, PROJECT_TITLE

tmpdir = setup_test_directory(temporary=True, populate_fmriprep=True)

CONFIG_FILE_PATH = str(tmpdir / "clpipe_config.json")
TARGET_DIR_PATH = str(tmpdir / "data_fmriprep")
OUTPUT_DIR_PATH = str(tmpdir / "data_postproc" / "postproc_normalize")
OUTPUT_SUFFIX = "_normalized"
LOG_DIR_PATH = str(tmpdir / "logs")

logging.basicConfig(level=logging.INFO)

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

def test_intensity_normalization_10000_global_median():
    intensity_normalization(rescaling_method=RESCALING_10000_GLOBALMEDIAN,
                            target_dir=TARGET_DIR_PATH,
                            median_intensity=None,
                            rescaling_factor=None,
                            output_dir=OUTPUT_DIR_PATH,
                            )

def test_intensity_normalization_100_voxel_mean():
    intensity_normalization(rescaling_method=RESCALING_100_VOXELMEAN,
                            target_dir=TARGET_DIR_PATH,
                            median_intensity=None,
                            rescaling_factor=None,
                            output_dir=OUTPUT_DIR_PATH,
                            )

def test_calculate_10000_global_median():
    image = None
    calculate_10000_global_median(image)

def test_calculate_100_voxel_mean():
    image = None
    calculate_100_voxel_mean(image)

if __name__ == "__main__":
    test_intensity_normalization_100_voxel_mean()