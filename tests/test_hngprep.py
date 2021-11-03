import sys
import pytest
import logging

from pathlib import Path
from click.testing import CliRunner

sys.path.append('../clpipe')
from clpipe.config_json_parser import ClpipeConfigParser
from conftest import NUM_SUBJECTS

CONFIG_FILE_PATH = "clpipe_config.json"
FMRI_PREPPED_SUFFIX = "_boldref"
LOG_DIR_PATH = "logs"

logging.basicConfig(level=logging.INFO)

@pytest.fixture(scope="module")
def clpipe_hngout_dir(clpipe_fmriprep_dir):
    """Fixture which adds an hngprep output folder"""

    normalized_folder = clpipe_fmriprep_dir / "data_hngprep"
    normalized_folder.mkdir()
    
    return clpipe_fmriprep_dir

@pytest.fixture(scope="module")
def hngprep_config(clpipe_config_default, clpipe_hngout_dir):
    """Fixture which sets up an intensity normalization enabled configuration object."""
    target_dir: Path = clpipe_hngout_dir / "data_fmriprep" / "fmriprep"
    output_dir: Path = clpipe_hngout_dir / "data_hngprep"

    clpipe_config_default.config['HNGPrepOptions']['TargetDirectory'] = str(target_dir)
    clpipe_config_default.config['HNGPrepOptions']['OutputDirectory'] = str(output_dir)
    clpipe_config_default.config['HNGPrepOptions']['TargetSuffix'] = "preproc_bold.nii.gz"
    clpipe_config_default.config['HNGPrepOptions']['OutputSuffix'] = "hngprep_bold.nii.gz"
    clpipe_config_default.config['HNGPrepOptions']['IntensityNormalizationMethod'] = "10000_globalmedian"
    clpipe_config_default.config['HNGPrepOptions']['LogDirectory'] = \
        clpipe_hngout_dir / "logs" / "hngprep_logs"

    return clpipe_config_default

@pytest.mark.skip(reason="Not yet needed")
def test_hngprep_cli(hngprep_config, clpipe_fmriprep_dir):
    runner = CliRunner()
    result = runner.invoke(
    hngprep_cli, 
    [
        '-normalization_method', "10000_globalmedian", 
        '-config_file', clpipe_fmriprep_dir / "clpipe_config.json",
        '-target_dir', hngprep_config.config['HNGPrepOptions']['TargetDirectory'],
        '-output_dir', hngprep_config.config['HNGPrepOptions']['OutputDirectory'], 
        '-output_suffix', hngprep_config.config['HNGPrepOptions']['OutputSuffix'], 
        '-log_dir', LOG_DIR_PATH,
        '-submit', True, 
        '-batch', False, 
        '-debug', True, 
    ])

    assert result.exit_code == 0

@pytest.mark.skip(reason="Not yet needed")
def test_hngprep_cli_None():
    runner = CliRunner()
    result = runner.invoke(
    hngprep_cli, 
    [
        '-normalization_method', "", 
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

@pytest.mark.skip(reason="Not yet needed")
def test_hngprep(hngprep_config, clpipe_fmriprep_dir):
    """Must create data_normalization folder."""
    hngprep(subjects=list(range(0, 8)),
            target_dir=hngprep_config.config['HNGPrepOptions']['TargetDirectory'],
            output_dir=hngprep_config.config['HNGPrepOptions']['OutputDirectory'],
            output_suffix=hngprep_config.config['HNGPrepOptions']['OutputSuffix'],
            config_file=clpipe_fmriprep_dir / "clpipe_config.json",
            normalization_method="100_voxelmean")

    count = 0
    for subject in (Path(hngprep_config.config['HNGPrepOptions']['OutputDirectory']) / "data_hngprep").iterdir():
        count += 1

    assert count == 8
