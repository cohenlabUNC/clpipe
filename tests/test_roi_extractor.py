import pytest
from clpipe.config.options import ProjectOptions
from pathlib import Path

from clpipe.roi_extractor import (
    fmri_roi_extraction,
    fmri_roi_extract_image,
    fmriprep_mask_finder,
    STEP_NAME,
)
from clpipe.utils import get_logger


def test_fmri_roi_extraction(config_file_postproc):
    """Basic test of roi_extraction using single run."""
    fmri_roi_extraction(
        subjects=["1"], single=False, config_file=config_file_postproc, debug=True
    )


def test_fmri_roi_extraction_overlap_ok(clpipe_postproc_dir):
    config_file_path = clpipe_postproc_dir / "clpipe_config.json"

    config: ProjectOptions = ProjectOptions.load(config_file_path)

    config.roi_extraction.overlap_ok = True
    config.dump(config_file_path)

    """Basic test of roi_extraction using single run."""
    fmri_roi_extraction(
        subjects=["1"], single=False, config_file=config_file_path, debug=True
    )


def test_fmri_roi_extraction_legacy(config_file_postproc_legacy_fmriprep):
    """Basic test of roi_extraction using single run
    on fmriprep version < 21"""
    fmri_roi_extraction(
        subjects=["1"],
        single=False,
        config_file=config_file_postproc_legacy_fmriprep,
        debug=True,
    )


def test_fmri_roi_extract_image(clpipe_postproc_dir, artifact_dir, request, helpers):
    """Given an fmriprep target image, test ROI extraction on a single subject - show output."""
    artifact_dir = helpers.create_test_dir(artifact_dir, request.node.name)

    logger = get_logger(STEP_NAME, debug=True, log_dir=clpipe_postproc_dir / "logs")
    image_name = "sub-1_task-gonogo_space-MNI152NLin2009cAsym_desc-postproc_bold.nii.gz"
    image_path = clpipe_postproc_dir / "data_postproc/default/sub-1/func" / image_name
    config_file_path = clpipe_postproc_dir / "clpipe_config.json"

    # Replace once new config is implemented
    config: ProjectOptions = ProjectOptions.load(config_file_path)
    config.roi_extraction.output_directory = artifact_dir

    Path(artifact_dir / "bigbrain").mkdir(exist_ok=True)

    fmri_roi_extract_image(
        str(image_path),
        config,
        "bigbrain",
        "clpipe/data/atlases/bigbrain/BigBrain300_MNI_coordinates.txt",
        "sphere",
        5,
        True,
        True,
        logger,
    )

def test_fmriprep_mask_finder(clpipe_postproc_dir):
    """Ensure that this function finds the correct fMRIPrep mask given
    a specific postprocessing image."""

    logger = get_logger(STEP_NAME, debug=True, log_dir=clpipe_postproc_dir / "logs")

    image_name = "sub-1_task-gonogo_space-MNI152NLin2009cAsym_desc-postproc_bold.nii.gz"
    image_path = (
        clpipe_postproc_dir
        / "data_postproc/default/sub-1/func" / image_name
    )
    config_file_path = clpipe_postproc_dir / "clpipe_config.json"

    config: ProjectOptions = ProjectOptions.load(config_file_path)

    matching_mask = fmriprep_mask_finder(
        image_path=image_path,
        config=config,
        logger=logger
    )

    assert Path(matching_mask).name == "sub-1_task-gonogo_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"



