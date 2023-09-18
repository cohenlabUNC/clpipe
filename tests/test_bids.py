import pytest
from pathlib import Path

from clpipe.bids import get_bids
from bids import BIDSLayout, BIDSLayoutIndexer


def test_get_bids(clpipe_fmriprep_dir):
    project_dir = clpipe_fmriprep_dir
    layout = get_bids(
        project_dir / "data_BIDS",
        database_path=project_dir / "BIDS_index",
        index_metadata=True,
    )
    index_sub_0_path = layout.get(subject="0", return_type="filename")[0]
    actual_sub_0_path = str(
        clpipe_fmriprep_dir / "data_BIDS/sub-0/func/sub-0_task-rest_bold.nii.gz"
    )
    assert index_sub_0_path == actual_sub_0_path


def test_get_bids_derivatives(clpipe_fmriprep_dir):
    project_dir = clpipe_fmriprep_dir
    layout = get_bids(
        project_dir / "data_BIDS",
        database_path=project_dir / "BIDS_index",
        index_metadata=True,
        fmriprep_dir=project_dir / "data_fmriprep",
    )

    index_sub_0_path = layout.get(subject="0", return_type="filename")[0]
    actual_sub_0_path = str(
        clpipe_fmriprep_dir / "data_BIDS/sub-0/func/sub-0_task-rest_bold.nii.gz"
    )
    assert index_sub_0_path == actual_sub_0_path
