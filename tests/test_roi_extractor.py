import pytest
from pathlib import Path

from clpipe.roi_extractor import (
    fmri_roi_extraction,
    fmri_roi_extract_image,
    STEP_NAME,
)
from clpipe.utils import get_logger


def test_fmri_roi_extraction(config_file_postproc2):
    """Basic test of roi_extraction using single run."""
    fmri_roi_extraction(
        subjects=["1"], single=True, config_file=config_file_postproc2, debug=True
    )


def test_fmri_roi_extraction_legacy(config_file_postproc2_legacy_fmriprep):
    """Basic test of roi_extraction using single run
    on fmriprep version < 21"""
    fmri_roi_extraction(
        subjects=["1"],
        single=True,
        config_file=config_file_postproc2_legacy_fmriprep,
        debug=True,
    )

def test_fmri_roi_extract_image(clpipe_postproc2_dir, artifact_dir, request, helpers):
    """Test ROI extraction on a single subject - show output."""
    artifact_dir = helpers.create_test_dir(artifact_dir, request.node.name)

    logger = get_logger(STEP_NAME, debug=True, log_dir=clpipe_postproc2_dir / "logs")
    image_name = "sub-1_task-gonogo_space-MNI152NLin2009cAsym_desc-postproc_bold.nii.gz"
    image_path = (
        clpipe_postproc2_dir
        / "data_postproc2/default/sub-1/func" / image_name
    )
    config_file_path = clpipe_postproc2_dir / "clpipe_config.json"

    # Replace once new config is implemented
    from clpipe.config_json_parser import ClpipeConfigParser
    configParser = ClpipeConfigParser()
    configParser.config_updater(config_file_path)

    configParser.config["ROIExtractionOptions"]["OutputDirectory"] = artifact_dir

    Path(artifact_dir / "bigbrain").mkdir(exist_ok=True)

    fmri_roi_extract_image(
        str(image_path),
        configParser,
        "bigbrain",
        "clpipe/data/atlases/bigbrain/BigBrain300_MNI_coordinates.txt",
        "sphere",
        5,
        True,
        True,
        logger,
    )

def test_fmri_roi_extract_image_fmriprep(clpipe_fmriprep_dir, artifact_dir, request, helpers):
    """Given an fmriprep target image, test ROI extraction on a single subject - show output."""
    artifact_dir = helpers.create_test_dir(artifact_dir, request.node.name)

    logger = get_logger(STEP_NAME, debug=True, log_dir=clpipe_fmriprep_dir / "logs")
    image_name = "sub-1_task-gonogo_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    image_path = (
        clpipe_fmriprep_dir
        / "data_fmriprep/sub-1/func" / image_name
    )
    config_file_path = clpipe_fmriprep_dir / "clpipe_config.json"

    # Replace once new config is implemented
    from clpipe.config_json_parser import ClpipeConfigParser
    configParser = ClpipeConfigParser()
    configParser.config_updater(config_file_path)

    configParser.config["ROIExtractionOptions"]["OutputDirectory"] = artifact_dir
    configParser.config["ROIExtractionOptions"]["TargetSuffix"] = "desc-preproc_bold.nii.gz"

    Path(artifact_dir / "bigbrain").mkdir(exist_ok=True)

    fmri_roi_extract_image(
        str(image_path),
        configParser,
        "bigbrain",
        "clpipe/data/atlases/bigbrain/BigBrain300_MNI_coordinates.txt",
        "sphere",
        5,
        True,
        True,
        logger,
    )
