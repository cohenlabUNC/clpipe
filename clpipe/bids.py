"""
BIDS dataset query and other helper functions
"""

from pathlib import Path
from .errors import (
    MixingFileNotFoundError,
    NoImagesFoundError,
    NoSubjectsFoundError,
    NoiseFileNotFoundError,
    SubjectNotFoundError,
)
import json
import warnings
import os

from bids import BIDSLayout, BIDSLayoutIndexer


def get_bids(
    bids_dir: os.PathLike,
    validate=False,
    database_path: os.PathLike = None,
    fmriprep_dir: os.PathLike = None,
    index_metadata=False,
    refresh=False,
    logger=None,
) -> BIDSLayout:
    try:
        database_path = Path(database_path)

        # Use an existing pybids database,
        #   and user did not request an index refresh
        if database_path.exists() and not refresh:
            if logger:
                logger.debug(f"Using existing BIDS index: {database_path}")
            return BIDSLayout(database_path=database_path)
        # Index from scratch (slow)
        else:
            indexer = BIDSLayoutIndexer(
                validate=validate, index_metadata=index_metadata
            )
            if logger:
                logger.info(f"Indexing BIDS directory: {bids_dir}")
                logger.info("This can take a few minutes...")

            if fmriprep_dir:
                # When setting derivative dir in this version of pybids, don't use
                #   the BIDSLayoutIndexer, pass through Layout instead - indexer
                #   ignores derivatives due to bug.
                # Ignore user warning about not using BIDSLayoutIndexer
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning)
                    return BIDSLayout(
                        bids_dir,
                        database_path=database_path,
                        derivatives=fmriprep_dir,
                        reset_database=refresh,
                        validate=validate,
                        index_metadata=index_metadata,
                    )
            else:
                return BIDSLayout(
                    bids_dir,
                    indexer=indexer,
                    database_path=database_path,
                    reset_database=refresh,
                )
    except FileNotFoundError as fne:
        if logger:
            logger.error(fne)
        raise fne


def get_subjects(bids_dir: BIDSLayout, subjects):
    # If no subjects were provided, use all subjects in the fmriprep directory
    if subjects is None or len(subjects) == 0:
        subjects = bids_dir.get_subjects(scope="derivatives")
        if len(subjects) == 0:
            no_subjects_found_str = f"No subjects found to parse at: {bids_dir.root}"
            raise NoSubjectsFoundError(no_subjects_found_str)

    return subjects


def get_images_to_process(
    subject_id, image_space, bids, logger, tasks=None, acquisitions=None
):
    logger.info(f"Searching for images to process")
    logger.info(f"Target image space: {image_space}")

    # Find the subject's preproc images
    try:
        images_to_process = []

        search_args = {
            "subject": subject_id,
            "extension": "nii.gz",
            "datatype": "func",
            "suffix": "bold",
            "desc": "preproc",
            "scope": "derivatives",
            "space": image_space,
        }
        if tasks:
            search_args["task"] = tasks
            logger.info(f"Targeting task(s): {tasks}")
        else:
            logger.info(f"Targeting all available tasks.")

        if acquisitions:
            search_args["acquisition"] = acquisitions
            logger.info(f"Targeting acquisition(s): {acquisitions}")
        else:
            logger.info(f"Targeting all available acquisitions.")

        images_to_process = bids.get(**search_args)

        if len(images_to_process) == 0:
            raise NoImagesFoundError(
                f"No preproc BOLD images found for sub-{subject_id} "
                f"in space {image_space}, task(s): {str(tasks)}."
            )

        logger.info(f"Found images: {len(images_to_process)}")
        return images_to_process
    except IndexError:
        raise NoImagesFoundError(
            f"No preproc BOLD image for subject {subject_id} found."
        )


def validate_subject_exists(bids, subject_id):
    # Open the bids dir and validate that it contains the subject
    if len(bids.get(subject=subject_id, scope="derivatives")) == 0:
        snfe = (
            f"Subject {subject_id} was not found in fmriprep output. "
            "You may need to add the option '-refresh_index' if this "
            "is a new subject."
        )
        raise SubjectNotFoundError(snfe)


def get_mixing_file(bids, query_params, logger):
    logger.info("Searching for MELODIC mixing file")
    try:
        mixing_file = bids.get(
            **query_params,
            suffix="mixing",
            extension=".tsv",
            return_type="filename",
            desc="MELODIC",
            scope="derivatives",
        )[0]
        logger.info(f"MELODIC mixing file found: {mixing_file}")

        return mixing_file
    except IndexError:
        raise MixingFileNotFoundError(
            (
                f"MELODIC mixing file for query {query_params} not found. "
                "Did you set UseAROMA to 'true' in your FMRIPrepOptions?"
            )
        )


def get_noise_file(bids, query_params, logger):
    logger.info("Searching for AROMA noise ICs file")
    try:
        noise_file = bids.get(
            **query_params,
            suffix="AROMAnoiseICs",
            extension=".csv",
            return_type="filename",
            scope="derivatives",
        )[0]
        logger.info((f"AROMA noise ICs file found: {noise_file}"))

        return noise_file
    except IndexError:
        raise NoiseFileNotFoundError(
            (
                f"AROMA noise ICs file for query {query_params} not found. "
                "Did you set UseAROMA to 'true' in your FMRIPrepOptions?"
            )
        )


def get_mask(bids, query_params, logger):
    # Find the subject's mask file
    logger.info("Searching for mask file")
    try:
        mask_image = bids.get(
            **query_params,
            suffix="mask",
            extension=".nii.gz",
            datatype="func",
            return_type="filename",
            desc="brain",
            scope="derivatives",
        )[0]
        logger.info(f"Mask file found: {mask_image}")

        return mask_image
    except IndexError:
        logger.warn(f"Mask image for search query: {query_params} not found")
        return None


def get_tr(bids, query_params, logger):
    # To get the TR, we do another, similar query to get the sidecar
    # and open it as a dict, because indexing metadata in
    # pybids is too slow to be worth just having the TR available
    # This can probably be done in just one query combined with the above

    image_to_process_json = bids.get(
        **query_params,
        extension=".json",
        datatype="func",
        suffix="bold",
        desc="preproc",
        scope="derivatives",
        return_type="filename",
    )[0]

    logger.info(f"Looking up TR in file: {image_to_process_json}")

    with open(image_to_process_json) as sidecar_file:
        sidecar_data = json.load(sidecar_file)
        tr = sidecar_data["RepetitionTime"]

        logger.info(f"Found TR: {tr}")

        return tr


def get_confounds(bids, query_params, logger):
    # Find the subject's confounds file

    logger.info("Searching for confounds file")
    try:
        confounds = bids.get(
            **query_params,
            return_type="filename",
            extension=".tsv",
            desc="confounds",
            scope="derivatives",
        )[0]
        logger.info(f"Confound file found: {confounds}")

        return confounds
    except IndexError:
        logger.warn(f"Confound file for query {query_params} not found.")
