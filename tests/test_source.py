from clpipe.source import flywheel_sync
from pathlib import Path


def test_flywheel_sync(clpipe_dicom_dir):
    """Test to ensure flywheel sync is working."""
    flywheel_sync(clpipe_dicom_dir / "clpipe_config.json", submit=False, debug=True)