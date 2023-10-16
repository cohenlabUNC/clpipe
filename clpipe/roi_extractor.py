import numpy as np
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from nilearn.input_data import NiftiSpheresMasker
    from nilearn.input_data import NiftiLabelsMasker
    from nilearn.input_data import NiftiMapsMasker
    from nilearn.image import concat_imgs
import os

import click
import json
import glob
import shutil
from .config.options import ProjectOptions
from .batch_manager import BatchManager, Job
from pkg_resources import resource_stream, resource_filename
from .errors import MaskFileNotFoundError
from .utils import get_logger, resolve_fmriprep_dir
from pathlib import Path

STEP_NAME = "roi_extraction"


def fmri_roi_extraction(
    subjects=None,
    config_file=None,
    target_dir=None,
    target_suffix=None,
    output_dir=None,
    task=None,
    log_output_dir=None,
    atlas_name=None,
    custom_atlas=None,
    custom_label=None,
    custom_type=None,
    radius="5",
    submit=False,
    single=False,
    overlap_ok=None,
    debug=False,
    overwrite=False,
):
    config = ProjectOptions.load(config_file)
    config.load_cli_args(
        target_directory=target_dir,
        target_suffix=target_suffix,
        output_directory=output_dir,
        log_directory=log_output_dir,
    )
    setup_dirs(config)

    logger = get_logger(STEP_NAME, debug=debug, log_dir=config.get_logs_dir())

    if not single:
        config_path = os.path.join(
            config.roi_extraction.output_directory, os.path.basename(config_file)
        )
        config.dump(config_path)
    else:
        config_path = ""
    if not subjects:
        sublist = [
            o.replace("sub-", "")
            for o in os.listdir(config.roi_extraction.target_directory)
            if os.path.isdir(os.path.join(config.roi_extraction.target_directory, o))
            and "sub-" in o
        ]
    else:
        sublist = subjects

    if atlas_name is not None:
        atlas_list = [atlas_name]
    else:
        atlas_list = config.roi_extraction.atlases

    with resource_stream(__name__, "data/atlasLibrary.json") as at_lib:
        atlas_library = json.load(at_lib)

    atlas_names = [atlas["atlas_name"] for atlas in atlas_library["Atlases"]]
    logger.debug(atlas_names)
    custom_radius = radius
    submission_string = (
        """fmri_roi_extraction -config_file={config} -atlas_name={atlas} -single"""
    )
    submission_string_custom = """fmri_roi_extraction -config_file={config} 
        -atlas_name={atlas} -custom_atlas={custom_atlas} -custom_label={custom_labels} 
        -custom_type={custom_type} -single"""

    batch_manager = BatchManager(config.batch_config_path, log_output_dir)
    batch_manager.update_mem_usage(config.roi_extraction.memory_usage)
    batch_manager.update_time(config.roi_extraction.time_usage)
    batch_manager.update_nthreads(config.roi_extraction.n_threads)
    batch_manager.update_email(config.email_address)
    batch_manager.createsubmissionhead()
    for subject in sublist:
        logger.info(f"Starting ROI extraction for suject: {subject}")
        for cur_atlas in atlas_list:
            custom_flag = False
            sphere_flag = False
            if type(cur_atlas) is dict:
                custom_flag = True
                atlas_name = cur_atlas["atlas_name"]
                logger.info(f"Using Custom Dict Atlas: {atlas_name}")
                custom_atlas = cur_atlas["atlas_file"]
                logger.debug(custom_atlas)
                custom_label = cur_atlas["atlas_labels"]
                logger.debug(custom_label)
                custom_type = cur_atlas["atlas_type"]
                logger.debug(custom_type)
                if "sphere" in custom_type:
                    logger.debug("Sphere flag: ON")
                    sphere_flag = True
                    custom_radius = cur_atlas["radius"]
                    logger.debug(custom_radius)
            else:
                atlas_name = cur_atlas
            logger.debug(atlas_name)
            if atlas_name in atlas_names:
                logger.debug("Found atlas name in library")
                index = atlas_names.index(atlas_name)
                atlas_filename = atlas_library["Atlases"][index]["atlas_file"]
                atlas_labels = atlas_library["Atlases"][index]["atlas_labels"]
                atlas_type = atlas_library["Atlases"][index]["atlas_type"]
                if "sphere" in atlas_type:
                    sphere_flag = True
            else:
                logger.debug("Did Not Find Atlas Name in Library")
                custom_flag = True
                if any(
                    [
                        not os.path.exists(custom_atlas),
                        not os.path.exists(custom_label),
                        custom_type not in ["label", "maps", "sphere"],
                    ]
                ):
                    raise ValueError(
                        "You are attempting to use a custom atlas, but have not "
                        "specified one or more of the following: \n"
                        "\t A custom atlas mask file (.nii or .nii.gz)"
                        "\t A custom atlas label file (a file with information about the atlas)"
                        "\t A custom atlas type (label, maps or spheres)"
                    )
                else:
                    atlas_filename = custom_atlas
                    atlas_labels = custom_label
                    atlas_type = custom_type
                    if "sphere" in custom_type:
                        sphere_flag = True
            if custom_flag:
                sub_string_temp = submission_string_custom.format(
                    config=config_path,
                    atlas=atlas_name,
                    custom_atlas=atlas_filename,
                    custom_labels=atlas_labels,
                    custom_type=atlas_type,
                )
            else:
                sub_string_temp = submission_string.format(
                    config=config_path,
                    atlas=atlas_name,
                )
            if sphere_flag:
                sub_string_temp = sub_string_temp + " -radius=" + custom_radius
            if task is not None:
                sub_string_temp = sub_string_temp + " -task=" + task
            if overlap_ok or config.roi_extraction.overlap_ok:
                sub_string_temp = sub_string_temp + " -overlap_ok"
                logger.debug("Overlap ok flag set")

            sub_string_temp = sub_string_temp + " " + subject
            batch_manager.addjob(
                Job("ROI_extract_" + subject + "_" + atlas_name, sub_string_temp)
            )
            if single:
                _fmri_roi_extract_subject(
                    subject,
                    task,
                    atlas_name,
                    atlas_filename,
                    atlas_labels,
                    atlas_type,
                    custom_radius,
                    custom_flag,
                    config,
                    overlap_ok,
                    overwrite,
                    logger,
                )
    if not single:
        if submit:
            batch_manager.compilejobstrings()
            batch_manager.submit_jobs()
        else:
            batch_manager.compilejobstrings()
            click.echo(batch_manager.print_jobs())


def _fmri_roi_extract_subject(
    subject,
    task,
    atlas_name,
    atlas_filename,
    atlas_label,
    atlas_type,
    radius,
    custom_flag,
    config: ProjectOptions,
    overlap_ok,
    overwrite,
    logger,
):
    logger.info(
        "Running Subject "
        + subject
        + " Atlas: "
        + atlas_name
        + " Atlas Type: "
        + atlas_type
    )

    if not custom_flag:
        atlas_path = resource_filename(__name__, atlas_filename)
        atlas_labelpath = resource_filename(__name__, atlas_label)
    else:
        atlas_path = os.path.abspath(atlas_filename)
        atlas_labelpath = os.path.abspath(atlas_label)
    logger.debug(f"Using atlas path: {atlas_path}")

    search_string = os.path.abspath(
        os.path.join(
            config.roi_extraction.target_directory,
            "sub-" + subject,
            "**",
            "*" + config.roi_extraction.target_suffix,
        )
    )
    logger.debug(search_string)
    subject_files = glob.glob(search_string, recursive=True)
    if task is not None:
        logger.info(f"Checking for task {task} for subjects: {subject_files}")
        subject_files = [x for x in subject_files if "task-" + task in x]
    logger.info(f"Processing subjects: {subject_files}")

    os.makedirs(
        os.path.join(config.roi_extraction.output_directory, atlas_name),
        exist_ok=True,
    )
    if not Path(atlas_labelpath).exists():
        shutil.copy2(atlas_labelpath, config.roi_extraction.output_directory)

    for file in subject_files:
        fmri_roi_extract_image(
            file,
            config,
            atlas_name,
            atlas_path,
            atlas_type,
            radius,
            overlap_ok,
            overwrite,
            logger,
        )


def fmri_roi_extract_image(
    file,
    config: ProjectOptions,
    atlas_name,
    atlas_path,
    atlas_type,
    radius,
    overlap_ok,
    overwrite,
    logger,
):
    logger.info(f"Processing image: {Path(file).stem}")
    file_outname = os.path.splitext(os.path.basename(file))[0]
    if ".nii" in file_outname:
        file_outname = os.path.splitext(file_outname)[0]

    if (
        os.path.exists(
            os.path.join(
                config.roi_extraction.output_directory,
                atlas_name + "/" + file_outname + "_atlas-" + atlas_name + ".csv",
            )
        )
        and not overwrite
    ):
        logger.info("File Exists! Skipping. Use -overwrite to reprocess.")
        return

    try:
        # First, try to find this image's mask.
        mask_file = _mask_finder(file, config, logger)
    except MaskFileNotFoundError:
        if config.roi_extraction.require_mask:
            # If a mask is required, return here due to missing mask.
            logger.warning("Skipping this scan due to missing brain mask.")
            return
        else:
            # Otherwise, continue on with a warning.
            logger.warning(
                "Unable to find a mask for this image. Extracting ROIs without using brain mask."
            )
            ROI_ts = _fmri_roi_extract_image(
                file, atlas_path, atlas_type, radius, overlap_ok, logger
            )
    else:
        try:
            logger.info("Starting masked ROI extraction...")
            # Attempt to run ROI extraction with mask
            ROI_ts = _fmri_roi_extract_image(
                file,
                atlas_path,
                atlas_type,
                radius,
                overlap_ok,
                logger,
                mask=mask_file,
            )
        except ValueError as ve:
            # Trigger fallback flag if any ROIs are outside of the mask region.
            logger.warning(ve.__str__() + ". Extracting ROIs without using brain mask.")
            logger.info("Starting non-masked ROI extraction...")
            ROI_ts = _fmri_roi_extract_image(
                file, atlas_path, atlas_type, radius, overlap_ok, logger
            )

        temp_mask = concat_imgs([mask_file, mask_file])
        mask_ROIs = _fmri_roi_extract_image(
            temp_mask, atlas_path, atlas_type, radius, overlap_ok, logger
        )
        mask_ROIs = np.nan_to_num(mask_ROIs)
        logger.debug(mask_ROIs[0])
        to_remove = [
            ind
            for ind, prop in np.ndenumerate(mask_ROIs[0])
            if prop < config.roi_extraction.prop_voxels
        ]
        logger.debug(to_remove)
        ROI_ts[:, to_remove] = np.nan

        # Save ROI masked threshold timeseries
        np.savetxt(
            os.path.join(
                os.path.join(
                    config.roi_extraction.output_directory,
                    atlas_name,
                ),
                file_outname + "_atlas-" + atlas_name + "_voxel_prop.csv",
            ),
            mask_ROIs[0],
            delimiter=",",
        )

    # Save the ROI timeseries
    np.savetxt(
        os.path.join(
            os.path.join(config.roi_extraction.output_directory, atlas_name),
            file_outname + "_atlas-" + atlas_name + ".csv",
        ),
        ROI_ts,
        delimiter=",",
    )

    logger.info("Extraction completed.")


def _fmri_roi_extract_image(
    data, atlas_path, atlas_type, radius, overlap_ok, logger, mask=None
):
    if "label" in atlas_type:
        logger.info("Extract type: label")
        label_masker = NiftiLabelsMasker(atlas_path, mask_img=mask)
        timeseries = label_masker.fit_transform(data)
    if "sphere" in atlas_type:
        atlas_path = np.loadtxt(atlas_path)
        logger.info("Extract type: sphere")
        logger.info(f"Sphere radius: {radius}mm")
        spheres_masker = NiftiSpheresMasker(
            atlas_path, float(radius), mask_img=mask, allow_overlap=overlap_ok
        )
        timeseries = spheres_masker.fit_transform(data)
    if "maps" in atlas_type:
        logger.info("Extract type: maps")
        maps_masker = NiftiMapsMasker(
            atlas_path, mask_img=mask, allow_overlap=overlap_ok
        )
        timeseries = maps_masker.fit_transform(data)
    timeseries[timeseries == 0.0] = np.nan

    return timeseries


def get_available_atlases():
    with resource_stream(__name__, "data/atlasLibrary.json") as at_lib:
        atlas_library = json.load(at_lib)

    for atlas in atlas_library["Atlases"]:
        print("Atlas Label: " + atlas["atlas_name"])
        print("Atlas Type: " + atlas["atlas_type"])
        print("Atlas Citation: " + atlas["atlas_citation"])
        print("")


def _mask_finder(data, config: ProjectOptions, logger):
    """Search for a mask in the fmriprep output directory matching
    the name of the image targeted for roi_extraction"""

    _, _, _, front_matter, type, path = _file_folder_generator(
        os.path.basename(data),
        "func",
        target_suffix=config.roi_extraction.target_suffix,
    )
    logger.debug(f"Target suffix: {config.roi_extraction.target_suffix}")
    logger.debug(
        f"Image components (front_matter, type, path): {front_matter, type, path}"
    )

    fmriprep_dir = resolve_fmriprep_dir(config.roi_extraction.target_directory)
    logger.debug(f"fMRIPrep dir: {fmriprep_dir}")

    target_mask = os.path.join(
        fmriprep_dir, path + "_" + type + "_desc-brain_mask.nii.gz"
    )
    logger.debug(f"Target mask: {target_mask}")
    if not os.path.exists(target_mask):
        logger.warn(f"No .nii.gz mask file found, searching for unzipped variant...")
        target_mask_unzipped = os.path.join(
            fmriprep_dir, path + "_" + type + "_desc-brain_mask.nii"
        )
        if not os.path.exists(target_mask_unzipped):
            raise MaskFileNotFoundError(f"No mask found on path: {target_mask}")
    logger.debug(f"Found matching mask: {target_mask}")
    return target_mask


def setup_dirs(config: ProjectOptions):
    os.makedirs(
        Path(config.roi_extraction.output_directory) / "postproc_default", exist_ok=True
    )
    os.makedirs(config.roi_extraction.log_directory, exist_ok=True)


def _file_folder_generator(basename, modality, target_suffix=None):
    """Function parses out a BIDS file name to find its sub-components.

    TODO: this addresses a need that many other modules of clpipe use
    as well, but in slightly different ways (see the GLM prepare functions).
    This function is rather specific / hard-coded and
        could use better generalization.
    We should look to provide a utility function to replace where
    this logic is used in roi_extract, and others.
    """

    if target_suffix is not None:
        basename = basename.replace(target_suffix, "")

    comps = basename.split("_")
    if comps[-1] is "":
        comps = comps[0:-1]
    sub = comps[0]
    ses = comps[1]
    try:
        # Try to grab 'space' if present
        front_matter = "_".join(comps[0:-1])
    except IndexError:
        front_matter = "_".join(comps[0:-2])
    type = comps[-1]
    if "ses-" in ses:
        path = os.path.join(sub, ses, modality, front_matter)
        return sub, ses, modality, front_matter, type, path
    else:
        ses = ""
        path = os.path.join(sub, modality, front_matter)
        return sub, ses, modality, front_matter, type, path
