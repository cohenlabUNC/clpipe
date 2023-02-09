import pytest
from pathlib import Path

def test_setup():
    
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