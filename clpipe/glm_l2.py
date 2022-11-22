import os
import logging
import shutil
from pathlib import Path
import pandas as pd

from .config import *
from .config_json_parser import GLMConfigParser
from .utils import get_logger


def glm_l2_preparefsf(glm_config_file=None, l2_name=None, debug=None):
    logger = get_logger(L1_PREPARE_FSF_COMMAND_NAME, debug=debug)

    glm_config = GLMConfigParser(glm_config_file)

    l2_block = [x for x in glm_config.config['Level2Setups'] \
        if x['ModelName'] == str(l2_name)]
    if len(l2_block) is not 1:
        raise ValueError("L2 model not found, or multiple entries found.")

    l2_block = l2_block[0]
    glm_setup_options = glm_config.config['GLMSetupOptions']

    _glm_l2_propagate(l2_block, glm_setup_options, logger)


def _glm_l2_propagate(l2_block, glm_setup_options, logger):
    subject_file = l2_block['SubjectFile']
    prototype_file = l2_block['FSFPrototype']
    
    logger.info(f"Reading subject file: {subject_file}")
    sub_tab = pd.read_csv(subject_file)

    logger.info(f"Opening prototype file: {prototype_file}")
    with open(prototype_file) as f:
        fsf_file_template=f.readlines()

    output_ind = [
        i for i,e in enumerate(fsf_file_template) if "set fmri(outputdir)" in e
    ]
    image_files_ind = [
        i for i,e in enumerate(fsf_file_template) if "set feat_files" in e
    ]
    regstandard_ind = [
        i for i, e in enumerate(fsf_file_template) if "set fmri(regstandard)" in e
    ]

    sub_tab = sub_tab.loc[sub_tab['L2_name'] == l2_block['ModelName']]

    fsf_names = sub_tab.fsf_name.unique()

    if not os.path.exists(l2_block['FSFDir']):
        os.mkdir(l2_block['FSFDir'])

    for fsf in fsf_names:
        try:
            new_fsf = fsf_file_template
            target_dirs = sub_tab.loc[sub_tab["fsf_name"] == fsf].feat_folders
            counter = 1
            logger.info("Creating " + fsf)
            for feat in target_dirs:
                if not os.path.exists(feat):
                    raise FileNotFoundError("Cannot find "+ feat)
                else:
                    _apply_mumford_workaround(feat, logger)
                    new_fsf[image_files_ind[counter - 1]] = "set feat_files(" + str(counter) + ") \"" + os.path.abspath(
                        feat) + "\"\n"
                    counter = counter + 1

            out_dir = os.path.join(l2_block['OutputDir'], fsf + ".gfeat")
            new_fsf[output_ind[0]] = "set fmri(outputdir) \"" + os.path.abspath(out_dir) + "\"\n"
            out_fsf = os.path.join(l2_block['FSFDir'],
                                   fsf + ".fsf")

            if glm_setup_options['ReferenceImage'] is not "":
                new_fsf[regstandard_ind[0]] = "set fmri(regstandard) \"" + os.path.abspath(glm_setup_options['ReferenceImage']) + "\"\n"

            with open(out_fsf, "w") as fsf_file:
                fsf_file.writelines(new_fsf)

        except Exception as err:
            logging.exception(err)


def glm_apply_mumford_workaround(glm_config_file=None, 
                                 l1_feat_folders_path=None,
                                 debug=False):

    logger = get_logger(APPLY_MUMFORD_COMMAND_NAME, debug=debug)
    if glm_config_file:
        glm_config = GLMConfigParser(glm_config_file).config
        l1_feat_folders_path = glm_config["Level1Setups"]["OutputDir"]
    logger.info(f"Applying Mumford workaround to: {l1_feat_folders_path}")

    logger.info(f"Applying Mumford workaround to: {l1_feat_folders_path}")
    for l1_feat_folder in os.scandir(l1_feat_folders_path):
        if os.path.isdir(l1_feat_folder):
            logger.info(f"Processing L1 FEAT folder: {l1_feat_folder.path}")
            _apply_mumford_workaround(l1_feat_folder, logger)

    logger.info(f"Finished applying Mumford workaround.")


def _apply_mumford_workaround(l1_feat_folder, logger):
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

    # Delete the reg_standard folder if it exists
    reg_standard_path = l1_feat_folder / "reg_standard"
    if reg_standard_path.exists():
        logger.debug(f"Removing: {reg_standard_path}")
        shutil.rmtree(reg_standard_path)

    try:
        # Grab the FSLDIR environment var to get path to standard matrices
        fsl_dir = Path(os.environ["FSLDIR"])
        identity_matrix_path = fsl_dir / 'etc/flirtsch/ident.mat'
        func_to_standard_path = \
            l1_feat_reg_folder / "example_func2standard.mat"
        mean_func_path = l1_feat_folder / 'mean_func.nii.gz'
        standard_path = l1_feat_reg_folder / "standard.nii.gz"

        # Copy over the standard identity matrix
        logger.debug((
            f"Copying identity matrix {identity_matrix_path}"
            f" to {func_to_standard_path}"))
        shutil.copy(identity_matrix_path, func_to_standard_path)

        # Copy in the mean_func image as the reg folder standard,
        # imitating multiplication with the identity matrix.
        logger.debug(
            f"Copying mean func image {mean_func_path} to {standard_path}")
        shutil.copy(mean_func_path, standard_path)
    except FileNotFoundError as e:
        print(e, "- skipping")




