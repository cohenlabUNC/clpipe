import pytest
from pathlib import Path
import os
from typing import List
from clpipe.config.options import BatchManagerConfig

from clpipe.project_setup import project_setup, SourceDataError
from clpipe.config.options import ProjectOptions

PROJECT_TITLE = "test_project"


def test_project_setup_no_source(tmp_path: Path):
    """Check that clpipe creates an empty data_DICOMs folder in the project
    directory when no source is provided.
    """
    project_setup(project_title=PROJECT_TITLE, project_dir=tmp_path)

    assert Path(tmp_path / "data_DICOMs").exists()
    assert Path(tmp_path / "clpipe_config.json").exists()

def test_project_setup_no_source_rel_path(tmp_path: Path):
    """Assure proper paths created in config when relative path provided."""
    os.chdir(tmp_path)

    project_setup(project_title=PROJECT_TITLE, project_dir=".")

    config: ProjectOptions = ProjectOptions().load(Path(tmp_path / "clpipe_config.json"))

    # Ensure absolute path was applied to config
    assert(not config.fmriprep.output_directory.startswith("."))


def test_project_setup_referenced_source(tmp_path: Path, source_data: Path):
    """Check that clpipe's generated config file references a specified source
    directory that is not within the clpipe project directory. This variant
    should not create a data_DICOMs directory.
    """
    project_setup(
        project_title=PROJECT_TITLE,
        project_dir=tmp_path,
        source_data=source_data,
        move_source_data=False,
        symlink_source_data=False,
        debug=False,
    )

    assert not Path(tmp_path / "data_DICOMs").exists() and Path(source_data).exists()


def test_project_setup_symlink_source(tmp_path: Path, source_data: Path):
    """Check that clpipe creates a data_DICOMs dir and symlinks it to the given
    source data.
    """

    project_setup(
        project_title=PROJECT_TITLE,
        project_dir=tmp_path,
        source_data=source_data,
        move_source_data=False,
        symlink_source_data=True,
        debug=False,
    )

    assert Path(tmp_path / "data_DICOMs").exists() and os.path.islink(
        tmp_path / "data_DICOMs"
    )


@pytest.mark.skip(reason="Feature Not implemented")
def test_project_setup_move_source(tmp_path: Path):
    """Note: this is currently NOT IMPLEMENTED in project setup.

    Check that clpipe creates a data_DICOMs dir and moves the data from a given
    source directory to this directory. Data should not remain in the source directory.

    project_setup(project_title="Test", project_dir="TestDir",
                  source_data="TestSource", move_source_data=True,
                  symlink_source_data=False, debug=False)
    """
    pass


def test_project_setup_symlink_and_move(tmp_path: Path):
    """Ensure exception thrown if users tries to both symlink and move source data."""

    with pytest.raises(SourceDataError):
        project_setup(
            project_title=PROJECT_TITLE,
            project_dir=tmp_path,
            move_source_data=True,
            symlink_source_data=True,
        )


def test_project_setup_symlink_no_source(tmp_path: Path):
    """Ensure exception thrown if users tries to symlink without a source."""

    with pytest.raises(SourceDataError):
        project_setup(
            project_title=PROJECT_TITLE, project_dir=tmp_path, symlink_source_data=True
        )


def test_project_setup_move_no_source(tmp_path: Path):
    """Ensure exception thrown if users tries to move without a source."""

    with pytest.raises(SourceDataError):
        project_setup(
            project_title=PROJECT_TITLE, project_dir=tmp_path, move_source_data=True
        )


def test_project_setup_pitt_profile(tmp_path: Path):
    """Check that clpipe creates an empty data_DICOMs folder in the project
    directory when no source is provided.
    """
    # Testing if the pitt profile gets correctly made.
    project_setup(project_title=PROJECT_TITLE, project_dir=tmp_path, profile="pitt")
    pitt_profile = Path(tmp_path / ".clpipe/batch_config.json")

    assert pitt_profile.exists()
    
    pitt_config: BatchManagerConfig = BatchManagerConfig.load(pitt_profile)
    assert pitt_config.submission_head == "bq"

def test_project_setup_missing_paths(clpipe_dir: Path, project_paths: List[Path]):
    """Check if any expected clpipe setup fails to create any expect folders or files."""
    missing = project_paths

    for path in clpipe_dir.glob("**/**/*"):
        rel_path = path.relative_to(clpipe_dir)
        if rel_path in project_paths:
            missing.remove(rel_path)

    assert len(missing) == 0, f"Missing expected paths: {missing}"


def test_project_setup_extra_paths(clpipe_dir: Path, project_paths: List[Path]):
    """Check to see if clpipe setup creates any extra, unexpected folders or files."""
    extra = []

    for path in clpipe_dir.glob("**/**/*"):
        rel_path = path.relative_to(clpipe_dir)
        if rel_path not in project_paths:
            extra.append(rel_path)

    assert len(extra) == 0, f"Project directory contains unexpected paths: {extra}"


@pytest.fixture()
def project_paths() -> List[Path]:
    """Provides a list of the paths expected from running project_setup.

    TODO: We should eventually just pull these constants from central config
    """

    data_BIDS = Path("data_BIDS")
    data_ROI_ts = Path("data_ROI_ts")
    logs = Path("logs")

    # List of expected relative project paths. Path is used over strings for os abstraction.
    return [
        Path("analyses"),
        Path("data_DICOMs"),
        data_BIDS,
        data_BIDS / ".bidsignore",
        data_BIDS / "dataset_description.json",
        data_BIDS / "participants.tsv",
        data_BIDS / "README",
        data_BIDS / "sourcedata",
        data_BIDS / "participants.json",
        data_BIDS / "CHANGES",
        data_BIDS / "code",
        data_BIDS / "derivatives",
        Path("data_fmriprep"),
        Path("data_onsets"),
        data_ROI_ts,
        Path("l1_feat_folders"),
        Path("l1_fsfs"),
        Path("l2_fsfs"),
        Path("l2_gfeat_folders"),
        logs,
        logs / "bids_validation_logs",
        logs / "DCM2BIDS_logs",
        logs / "FMRIprep_logs",
        logs / "glm_logs",
        logs / "glm_logs" / "L1_launch",
        logs / "glm_logs" / "L2_launch",
        logs / "ROI_extraction_logs",
        logs / "clpipe.log",
        Path("scripts"),
        Path("clpipe_config.json"),
        Path("conversion_config.json"),
        Path("glm_config.json"),
        Path("l2_sublist.csv"),
        Path(".clpipe"),
        Path(".clpipe/batch_config.json")
    ]
