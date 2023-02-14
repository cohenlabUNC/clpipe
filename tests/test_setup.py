import pytest
from pathlib import Path

from clpipe.project_setup import project_setup

PROJECT_TITLE = "test_project"

def test_setup_no_source(project_dir):
    """Check that clpipe creates an empty data_DICOMs folder in the project
    directory when no source is provided.
    """
    
    project_setup(project_title=PROJECT_TITLE, project_dir=project_dir)

    assert Path(project_dir / "data_DICOMs").exists()


def test_setup_referenced_source(project_dir):
    """Check that clpipe's generated config file references a specified source
    directory that is not within the clpipe project directory. This variant
    should not create a data_DICOMs directory.
    
    project_setup(project_title="Test", project_dir="TestDir", 
                  source_data="TestSource", move_source_data=False,
                  symlink_source_data=False, debug=False)
    """
    assert False


def test_setup_symlink_source(project_dir):
    """Check that clpipe creates a data_DICOMs dir and symlinks it to the given
    source data.

    project_setup(project_title="Test", project_dir="TestDir", 
                  source_data="TestSource", move_source_data=False,
                  symlink_source_data=True, debug=False)
    """
    assert False


@pytest.mark.skip(reason="Feature Not implemented")
def test_setup_move_source(project_dir):
    """Note: this is currently NOT IMPLEMENTED in project setup.
    
    Check that clpipe creates a data_DICOMs dir and moves the data from a given
    source directory to this directory. Data should not remain in the source directory.
    
    project_setup(project_title="Test", project_dir="TestDir", 
                  source_data="TestSource", move_source_data=True,
                  symlink_source_data=False, debug=False)
    """
    pass


def test_setup_missing(clpipe_dir, project_paths):
    """Check if any expected clpipe setup fails to create any expect folders or files."""    
    missing = project_paths
    
    for path in clpipe_dir.glob('**/**/*'):
        rel_path = path.relative_to(clpipe_dir)
        if rel_path in project_paths:
            missing.remove(rel_path)
        
    assert len(missing) == 0, f"Missing expected paths: {missing}"


def test_setup_extra(clpipe_dir, project_paths):
    """Check to see if clpipe setup creates any extra, unexpected folders or files."""
    extra = []

    for path in clpipe_dir.glob('**/**/*'):
        rel_path = path.relative_to(clpipe_dir)
        if rel_path not in project_paths:
            extra.append(rel_path)
        
    assert len(extra) == 0, f"Project directory contains unexpected paths: {extra}"


@pytest.fixture()
def project_paths():
    # TODO: We should eventually just pull these constants from central config

    data_BIDS = Path("data_BIDS")
    data_postproc = Path("data_postproc")
    data_ROI_ts = Path("data_ROI_ts")
    logs = Path("logs")

    """List of expected relative project paths. Path is used over strings for os abstraction."""
    return [
        Path("analyses"),
        Path("data_DICOMs"),
        data_BIDS,
        data_BIDS / 'code',
        data_BIDS / 'derivatives',
        data_BIDS / 'sourcedata',
        data_BIDS / 'dataset_description.json',
        data_BIDS / 'participants.json',
        data_BIDS / 'participants.tsv',
        data_BIDS / 'README',
        data_BIDS / 'CHANGES',
        data_BIDS / '.bidsignore',
        Path("data_fmriprep"),
        Path("data_GLMPrep"),
        Path("data_onsets"),
        data_postproc,
        data_postproc / "betaseries_default",
        data_postproc / "postproc_default",
        data_ROI_ts,
        data_ROI_ts / 'postproc_default',
        Path("l1_feat_folders"),
        Path("l1_fsfs"),
        Path("l2_fsfs"),
        Path("l2_gfeat_folders"),
        Path("logs"),
        logs / "betaseries_logs",
        logs / "bids_validation_logs",
        logs / "DCM2BIDS_logs",
        logs / "glm_setup_logs",
        logs / "postproc_logs",
        logs / "ROI_extraction_logs",
        logs / "SUSAN_logs",
        logs / "clpipe.log",
        Path("scripts"),
        Path("clpipe_config.json"),
        Path("conversion_config.json"),
        Path("glm_config.json"),
        Path("l2_sublist.csv")
    ]