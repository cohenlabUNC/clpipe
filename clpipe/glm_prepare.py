"""
Design

Step 1: Load in prototype, identify all needed lines
Step 2: Load in paths for all image files, exclude/include as needed
Step 3: Run through all required image files, construct the file changes
Step 3a: Change prototype and spit out into fsf output folder
Step 4: Launch a feat job for each fsf
"""

import os
import glob
import sys
import nibabel as nib
import pandas as pd
import shutil
from pathlib import Path

from .config.glm import *
from .utils import get_logger
from .errors import *

STEP_NAME = "prepare"
APPLY_MUMFORD_STEP_NAME = "apply_mumford"
DEPRECATION_MSG = "WARNING: Using deprecated GLM setup file."
L2_SUBLIST_CSV_FILE_NAME = "l2_sublist.csv"
L2_SUBLIST_CSV_PATH = f"data/{L2_SUBLIST_CSV_FILE_NAME}"


def glm_prepare(
    glm_config_file: str = None, level: int = L1, model: str = None, debug: bool = False
):
    glm_config = GLMOptions(glm_config_file)
    setup_dirs(glm_config)

    warn_deprecated = False
    try:
        # These working indicates the user has a glm_config file from < v1.7.4
        # In this case, use the GLMSetupOptions block as root dict
        # TODO: when we get centralized config classes, this can be handled there
        task_name = glm_config.config["GLMSetupOptions"]["TaskName"]
        reference_image = glm_config.config["GLMSetupOptions"]["ReferenceImage"]
        warn_deprecated = True
    except KeyError:
        task_name = glm_config.config["TaskName"]
        reference_image = glm_config.config["ReferenceImage"]

    logger = get_logger(
        STEP_NAME, debug=debug, log_dir=glm_config.parent_options.get_logs_dir()
    )

    if warn_deprecated:
        logger.warn(DEPRECATION_MSG)

    if level in VALID_L1:
        level = L1
        setup = "Level1Setups"
    elif level in VALID_L2:
        level = L2
        setup = "Level2Setups"
    else:
        logger.error(f"Level must be {L1} or {L2}")
        sys.exit(1)

    logger.info(f"Preparing .fsfs for {level} model: {model}")
    logger.info(f"Targeting task: {task_name}")

    block = [x for x in glm_config.config[setup] if x["ModelName"] == str(model)]
    if len(block) is not 1:
        raise ValueError("Model not found, or multiple entries found.")
    model_options = block[0]

    if level == L1:
        if not Path(model_options["EVDirectory"]).exists():
            logger.error(
                f"EV Directory: {model_options['EVDirectory']} does not exist."
            )
            sys.exit(1)

        _glm_l1_propagate(model_options, task_name, reference_image, logger)
        sys.exit(0)
    elif level == L2:
        try:
            _glm_l2_propagate(model_options, reference_image, logger)
            sys.exit(0)
        except ModelNotFoundError as mnfe:
            logger.error(mnfe)
            sys.exit(1)


def _glm_l1_propagate(l1_block, task_name, reference_image, logger):
    with open(l1_block["FSFPrototype"]) as f:
        fsf_file_template = f.readlines()

    output_ind = [
        i for i, e in enumerate(fsf_file_template) if "set fmri(outputdir)" in e
    ]
    image_files_ind = [
        i for i, e in enumerate(fsf_file_template) if "set feat_files" in e
    ]
    ev_file_inds = [
        i for i, e in enumerate(fsf_file_template) if "set fmri(custom" in e
    ]
    confound_file_ind = [
        i for i, e in enumerate(fsf_file_template) if "set confoundev_files(1)" in e
    ]
    regstandard_ind = [
        i for i, e in enumerate(fsf_file_template) if "set fmri(regstandard)" in e
    ]
    tps_inds = [i for i, e in enumerate(fsf_file_template) if "set fmri(npts)" in e]
    if (
        l1_block["ImageIncludeList"] is not ""
        and l1_block["ImageExcludeList"] is not ""
    ):
        raise ValueError(
            "Only one of ImageIncludeList and ImageExcludeList should be non-empty"
        )

    image_files = glob.glob(
        os.path.join(l1_block["TargetDirectory"], "**", "*" + l1_block["TargetSuffix"]),
        recursive=True,
    )

    if l1_block["ImageIncludeList"] is not "":
        image_files = [
            file_path
            for file_path in image_files
            if os.path.basename(file_path) in l1_block["ImageIncludeList"]
        ]
        base_names = [os.path.basename(file_path) for file_path in image_files]

        files_not_found = [
            file for file in base_names if file not in l1_block["ImageIncludeList"]
        ]
        if len(files_not_found):
            logger.warning("Did not find the following files: " + str(files_not_found))

    if l1_block["ImageExcludeList"] is not "":
        image_files = [
            file_path
            for file_path in image_files
            if os.path.basename(file_path) not in l1_block["ImageExcludeList"]
        ]

    image_files = [file for file in image_files if "task-" + task_name in file]

    if not os.path.exists(l1_block["FSFDir"]):
        os.mkdir(l1_block["FSFDir"])

    if len(image_files) < 1:
        logger.info(
            "No image files found. Check your model's TargetDirectory, TargetSuffix, ImageIncludeList, and ImageExludeList settings."
        )
    else:
        logger.info("Propogating fsf files...")
        for file in image_files:
            try:
                file_name = os.path.basename(file)

                logger.info("Creating FSF File for image: " + file_name)
                img_data = nib.load(file)
                total_tps = img_data.shape[3]
                ev_conf = _get_ev_confound_mat(file, l1_block, logger)
                out_dir = os.path.join(
                    l1_block["OutputDir"],
                    file_name.replace("_" + l1_block["TargetSuffix"], ".feat"),
                )
                out_fsf = os.path.join(
                    l1_block["FSFDir"],
                    file_name.replace("_" + l1_block["TargetSuffix"], ".fsf"),
                )
                new_fsf = fsf_file_template

                new_fsf[tps_inds[0]] = "set fmri(npts) " + str(total_tps) + "\n"
                new_fsf[output_ind[0]] = (
                    'set fmri(outputdir) "' + os.path.abspath(out_dir) + '"\n'
                )
                new_fsf[image_files_ind[0]] = (
                    'set feat_files(1) "' + os.path.abspath(file) + '"\n'
                )

                if reference_image is not "":
                    new_fsf[regstandard_ind[0]] = (
                        'set fmri(regstandard) "'
                        + os.path.abspath(reference_image)
                        + '"\n'
                    )
                if l1_block["ConfoundSuffix"] is not "":
                    new_fsf[confound_file_ind[0]] = (
                        'set confoundev_files(1) "'
                        + os.path.abspath(ev_conf["Confounds"])
                        + '"\n'
                    )

                for i, e in enumerate(ev_conf["EVs"]):
                    new_fsf[ev_file_inds[i]] = (
                        "set fmri(custom"
                        + str(i + 1)
                        + ') "'
                        + os.path.abspath(e)
                        + '"\n'
                    )

                with open(out_fsf, "w") as fsf_file:
                    fsf_file.writelines(new_fsf)

            except (EVFileNotFoundError, ConfoundsNotFoundError) as nfe:
                logger.warn(nfe)

        logger.info("Propogation completed.")


def _get_ev_confound_mat(file, l1_block, logger):
    file_name = os.path.basename(file)

    file_prefix = os.path.basename(file).replace(l1_block["TargetSuffix"], "")

    EV_files = []
    for EV in l1_block["EVFileSuffices"]:
        try:
            search_path = os.path.join(l1_block["EVDirectory"], "**", file_prefix + EV)
            logger.debug(f"EV search path: {search_path}")
            search_results = glob.glob((search_path), recursive=True)
            if len(search_results) < 1:
                raise EVFileNotFoundError(f"EV file not found: {EV}")
            elif len(search_results) > 1:
                raise EVFileNotFoundError(
                    f"Found more than one EV file matching pattern: {search_path}"
                )
            EV_files.append(search_results[0])
        except EVFileNotFoundError as evfnfe:
            logger.debug(evfnfe)

    if len(EV_files) is not len(l1_block["EVFileSuffices"]):
        raise EVFileNotFoundError(
            (
                f"Did not find enough EV files for image: {file_name}. "
                f"Only found {len(EV_files)} and need "
                f"{len(l1_block['EVFileSuffices'])}"
            )
        )

    if l1_block["ConfoundSuffix"] is not "":
        search_path = os.path.join(
            l1_block["ConfoundDirectory"],
            "**",
            file_prefix + l1_block["ConfoundSuffix"],
        )
        logger.debug(f"Confound search path: {search_path}")
        search_results = glob.glob((search_path), recursive=True)
        if len(search_results) < 1:
            raise ConfoundsNotFoundError(
                f"Did not find a confound file for image: {file_name}"
            )
        elif len(search_results) > 1:
            raise ConfoundsNotFoundError(
                f"Found more than one confounds file matching pattern: {search_path}"
            )
        return {"EVs": EV_files, "Confounds": search_results[0]}

    return {"EVs": EV_files}


def _glm_l2_propagate(l2_block, reference_image, logger):
    subject_file = l2_block["SubjectFile"]
    prototype_file = l2_block["FSFPrototype"]

    logger.info(f"Reading subject file: {subject_file}")
    sub_tab = pd.read_csv(subject_file)

    sub_tab = sub_tab.loc[sub_tab["L2_name"] == l2_block["ModelName"]]

    fsf_names = sub_tab.fsf_name.unique()

    if len(fsf_names) == 0:
        raise ModelNotFoundError(
            f"No records found in subject file for model: {l2_block['ModelName']}"
        )

    logger.info(f"Opening prototype file: {prototype_file}")
    with open(prototype_file) as f:
        fsf_file_template = f.readlines()

    output_ind = [
        i for i, e in enumerate(fsf_file_template) if "set fmri(outputdir)" in e
    ]
    image_files_ind = [
        i for i, e in enumerate(fsf_file_template) if "set feat_files" in e
    ]
    regstandard_ind = [
        i for i, e in enumerate(fsf_file_template) if "set fmri(regstandard)" in e
    ]

    if not os.path.exists(l2_block["FSFDir"]):
        os.mkdir(l2_block["FSFDir"])

    error_count = 0

    logger.info("Propogating fsf files...")
    for fsf in fsf_names:
        try:
            new_fsf = fsf_file_template
            target_dirs = sub_tab.loc[sub_tab["fsf_name"] == fsf].feat_folders
            counter = 1
            logger.info("Creating L2 fsf file: " + fsf)
            for feat in target_dirs:
                if not os.path.exists(feat):
                    error_count += 1
                    raise FileNotFoundError(
                        "ERROR: Could not find L1 FEAT directory:  " + feat
                    )
                else:
                    _apply_mumford_workaround(feat, logger, remove_reg_standard=True)
                    new_fsf[image_files_ind[counter - 1]] = (
                        "set feat_files("
                        + str(counter)
                        + ') "'
                        + os.path.abspath(feat)
                        + '"\n'
                    )
                    counter = counter + 1

            out_dir = os.path.join(l2_block["OutputDir"], fsf + ".gfeat")
            new_fsf[output_ind[0]] = (
                'set fmri(outputdir) "' + os.path.abspath(out_dir) + '"\n'
            )
            out_fsf = os.path.join(l2_block["FSFDir"], fsf + ".fsf")

            if reference_image is not "":
                new_fsf[regstandard_ind[0]] = (
                    'set fmri(regstandard) "' + os.path.abspath(reference_image) + '"\n'
                )

            with open(out_fsf, "w") as fsf_file:
                fsf_file.writelines(new_fsf)

        except FileNotFoundError as err:
            logger.warn(err)

    error_msg = ""
    if error_count > 0:
        error_msg = f" with {error_count} error(s)"

    logger.info(f"Job completed{error_msg}")


def glm_apply_mumford_workaround(
    glm_config_file=None,
    l1_feat_folders_path=None,
    remove_reg_standard=False,
    debug=False,
):
    logger = get_logger(APPLY_MUMFORD_STEP_NAME, debug=debug)
    if glm_config_file:
        glm_config = GLMOptions(glm_config_file).config
        l1_feat_folders_path = glm_config["Level1Setups"]["OutputDir"]

    logger.info(f"Applying Mumford workaround to: {l1_feat_folders_path}")
    for l1_feat_folder in os.scandir(l1_feat_folders_path):
        if os.path.isdir(l1_feat_folder):
            logger.info(f"Processing L1 FEAT folder: {l1_feat_folder.path}")
            _apply_mumford_workaround(
                l1_feat_folder, logger, remove_reg_standard=remove_reg_standard
            )

    logger.info(f"Finished applying Mumford workaround.")


def _apply_mumford_workaround(l1_feat_folder, logger, remove_reg_standard=False):
    """
    When using an image registration other than FSL's, such as fMRIPrep's,
    this work-around is necessary to run FEAT L2 analysis in FSL.

    See: https://mumfordbrainstats.tumblr.com/post/166054797696/
        feat-registration-workaround
    """
    l1_feat_folder = Path(l1_feat_folder)
    l1_feat_reg_folder = l1_feat_folder / "reg"

    # Create the reg directory if it doesn't exist
    # This happens if FEAT's preprocessing was not used
    if not l1_feat_reg_folder.exists():
        l1_feat_reg_folder.mkdir()
    else:
        # Remove all of the .mat files in the reg folder
        for mat in l1_feat_reg_folder.glob("*.mat"):
            logger.debug(f"Removing: {mat}")
            os.remove(mat)

    if remove_reg_standard:
        # Delete the reg_standard folder if it exists
        reg_standard_path = l1_feat_folder / "reg_standard"
        if reg_standard_path.exists():
            logger.debug(f"Removing: {reg_standard_path}")
            shutil.rmtree(reg_standard_path)

    try:
        # Grab the FSLDIR environment var to get path to standard matrices
        fsl_dir = Path(os.environ["FSLDIR"])
        identity_matrix_path = fsl_dir / "etc/flirtsch/ident.mat"
        func_to_standard_path = l1_feat_reg_folder / "example_func2standard.mat"
        mean_func_path = l1_feat_folder / "mean_func.nii.gz"
        standard_path = l1_feat_reg_folder / "standard.nii.gz"

        # Copy over the standard identity matrix
        logger.debug(
            (
                f"Copying identity matrix {identity_matrix_path}"
                f" to {func_to_standard_path}"
            )
        )
        shutil.copyfile(identity_matrix_path, func_to_standard_path)

        # Copy in the mean_func image as the reg folder standard,
        # imitating multiplication with the identity matrix.
        logger.debug(f"Copying mean func image {mean_func_path} to {standard_path}")
        shutil.copyfile(mean_func_path, standard_path)
    except FileNotFoundError as e:
        print(e, "- skipping")


def setup_dirs(glm_config: GLMOptions):
    """Populates the GLM config file with resource paths based on project root dir."""
    from pkg_resources import resource_filename
    import shutil

    # Copy over an example L2 csv
    l2_csv = os.path.join(
        glm_config.parent_options.project_directory, L2_SUBLIST_CSV_FILE_NAME
    )
    if not os.path.exists(l2_csv):
        shutil.copyfile(resource_filename("clpipe", L2_SUBLIST_CSV_PATH), l2_csv)

    # Create default directories
    os.makedirs(glm_config.config["Level1Setups"][0]["FSFDir"], exist_ok=True)
    os.makedirs(glm_config.config["Level1Setups"][0]["EVDirectory"], exist_ok=True)
    os.makedirs(glm_config.config["Level1Setups"][0]["OutputDir"], exist_ok=True)
    os.makedirs(glm_config.config["Level2Setups"][0]["FSFDir"], exist_ok=True)
    os.makedirs(glm_config.config["Level2Setups"][0]["OutputDir"], exist_ok=True)
    os.makedirs(glm_config.config["Level1Setups"][0]["LogDir"], exist_ok=True)
    os.makedirs(glm_config.config["Level2Setups"][0]["LogDir"], exist_ok=True)
