import sys
sys.path.append('../clpipe')

import pytest
from pathlib import Path

def test_setup_project_missing(clpipe_dir, project_paths):
    
    missing = project_paths
    
    for path in clpipe_dir.glob('**/**/*'):
        rel_path = path.relative_to(clpipe_dir)
        if rel_path in project_paths:
            missing.remove(rel_path)
        
    assert len(missing) == 0, f"Missing expected paths: {missing}"

def test_setup_project_extra(clpipe_dir, project_paths):
    
    extra = []

    for path in clpipe_dir.glob('**/**/*'):
        rel_path = path.relative_to(clpipe_dir)
        if rel_path not in project_paths:
            extra.append(rel_path)
        
    assert len(extra) == 0, f"Project directory contains unexpected paths: {extra}"


@pytest.fixture()
def project_paths():
    """List of expected relative project paths. Path is used over strings for os abstraction."""
    return [
        Path("analyses"),
        Path("data_DICOMs"),
        Path("data_BIDS"),
        Path('data_BIDS/code'),
        Path('data_BIDS/derivatives'),
        Path('data_BIDS/sourcedata'),
        Path('data_BIDS/dataset_description.json'),
        Path('data_BIDS/participants.json'),
        Path('data_BIDS/participants.tsv'),
        Path('data_BIDS/README'),
        Path('data_BIDS/CHANGES'),
        Path("data_fmriprep"),
        Path("data_GLMPrep"),
        Path("data_onsets"),
        Path("data_postproc"),
        Path("data_postproc", "betaseries_default"),
        Path("data_postproc", "betaseries_noGSR"),
        Path("data_postproc", "betaseries_noScrub"),
        Path("data_postproc", "postproc_default"),
        Path("data_postproc", "postproc_noGSR"),
        Path("data_postproc", "postproc_noScrub"),
        Path("data_postproc", "normalized"),
        Path("data_ROI_ts"),
        Path('data_ROI_ts/postproc_default'),
        Path("l1_feat_folders"),
        Path("l1_fsfs"),
        Path("l2_fsfs"),
        Path("l2_gfeat_folders"),
        Path("logs"),
        Path("logs", "betaseries_logs"),
        Path("logs", "DCM2BIDS_logs"),
        Path("logs", "glm_setup_logs"),
        Path("logs", "postproc_logs"),
        Path("logs", "ROI_extraction_logs"),
        Path("logs", "SUSAN_logs"),
        Path("scripts"),
        Path("clpipe_config.json"),
        Path("conversion_config.json"),
        Path("glm_config.json"),
        Path("l2_sublist.csv")
    ]