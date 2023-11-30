import pytest
from pathlib import Path

from clpipe.convert2bids import convert2bids


def test_dcm2bids(clpipe_dicom_dir: Path, config_file: Path):
    convert2bids(
        config_file=config_file,
        dicom_dir=clpipe_dicom_dir / "sub",
        dicom_dir_format="{subject}",
    )


def test_dcm2bids_sub_session(clpipe_dicom_dir: Path, config_file: Path):
    convert2bids(
        config_file=config_file,
        dicom_dir=clpipe_dicom_dir / "sub_session",
        dicom_dir_format="{subject}/{session}",
    )


def test_dcm2bids_sub_session_flat(clpipe_dicom_dir: Path, config_file: Path):
    convert2bids(
        config_file=config_file,
        dicom_dir=clpipe_dicom_dir / "sub_session_flat",
        dicom_dir_format="{subject}_{session}",
    )


def test_dcm2bids_session_sub(clpipe_dicom_dir: Path, config_file: Path):
    convert2bids(
        config_file=config_file,
        dicom_dir=clpipe_dicom_dir / "session_sub",
        dicom_dir_format="{session}/{subject}",
    )


def test_dcm2bids_session_sub_flat(clpipe_dicom_dir: Path, config_file: Path):
    convert2bids(
        config_file=config_file,
        dicom_dir=clpipe_dicom_dir / "session_sub_flat",
        dicom_dir_format="{session}_{subject}",
    )


def test_heudiconv(clpipe_dicom_dir: Path, config_file: Path):
    convert2bids(
        config_file=config_file,
        dicom_dir=clpipe_dicom_dir / "sub",
        dicom_dir_format="{subject}",
        conv_config_file="heuristic.py"
    )


def test_convert2bids_local(clpipe_dicom_dir: Path, config_file: Path):
    convert2bids(
        dcm2bids=True,
        config_file=config_file,
        dicom_dir=clpipe_dicom_dir / "sub",
        dicom_dir_format="{subject}",
        batch=False,
    )
