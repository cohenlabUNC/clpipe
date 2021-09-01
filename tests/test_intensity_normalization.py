import sys
sys.path.append('../clpipe')

from clpipe.intensity_normalization import intensity_normalization
from testing_tools import setup_test_directory
from pathlib import Path


def test_intensity_normalization(tmpdir: Path):
    intensity_normalization(config_file=tmpdir / "clpipe_config.json",
                            target_dir=tmpdir / "data_fmriprep",
                            output_dir=tmpdir / "data_postproc/intensity_normalized",
                            output_suffix=tmpdir / "normalized",
                            log_dir=tmpdir / "logs/intensity_normaliztion",
                            submit=False,
                            batch=False,
                            debug=True)

def test_intensity_normalization_None():
    intensity_normalization(config_file=None,
                            target_dir=None,
                            output_dir=None,
                            output_suffix=None,
                            log_dir=None,
                            submit=False,
                            batch=False,
                            debug=True)

if __name__ == "__main__":
    tmpdir = setup_test_directory(populate_fmriprep=True)
    test_intensity_normalization(tmpdir)