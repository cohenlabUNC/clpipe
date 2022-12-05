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

from .config_json_parser import GLMConfigParser, ClpipeConfigParser
from .utils import add_file_handler, get_logger
from .config import *
from .errors import ConfoundsNotFoundError, EVFileNotFoundError

STEP_NAME = "prepare"

def glm_prepare(glm_config_file: str=None, level: int=L1,
                model: str=None, debug: bool=False):
    glm_config_parser = GLMConfigParser(glm_config_file)
    glm_config = glm_config_parser.config
    glm_setup_options = glm_config["GLMSetupOptions"]
    parent_config = glm_setup_options["ParentClpipeConfig"]

    config = ClpipeConfigParser()
    config.config_updater(parent_config)

    project_dir = config.config["ProjectDirectory"]
    add_file_handler(os.path.join(project_dir, "logs"))
    logger = get_logger(STEP_NAME, debug=debug)

    if level in VALID_L1:
        level = L1
        setup = 'Level1Setups'
    elif level in VALID_L2:
        level = L2
        setup = 'Level2Setups'
    else:
        logger.error(f"Level must be {L1} or {L2}")
        sys.exit(0)

    logger.info(f"Targeting task-{glm_setup_options['TaskName']} {level} model: {model}")
    logger.info("Propogating fsf files...")

    block = [x for x in glm_config[setup] \
            if x['ModelName'] == str(model)]
    if len(block) is not 1:
        raise ValueError("Model not found, or multiple entries found.")
    model_options = block[0]

    if level == L1:
        _glm_l1_propagate(model_options, glm_setup_options, logger)
    elif level == L2:
        pass


def _glm_l1_propagate(l1_block, glm_setup_options, logger):
    with open(l1_block['FSFPrototype']) as f:
        fsf_file_template=f.readlines()

    output_ind = [i for i,e in enumerate(fsf_file_template) if "set fmri(outputdir)" in e]
    image_files_ind = [i for i,e in enumerate(fsf_file_template) if "set feat_files" in e]
    ev_file_inds = [i for i,e in enumerate(fsf_file_template) if "set fmri(custom" in e]
    confound_file_ind = [i for i,e in enumerate(fsf_file_template) if "set confoundev_files(1)" in e]
    regstandard_ind = [i for i, e in enumerate(fsf_file_template) if "set fmri(regstandard)" in e]
    tps_inds = [i for i, e in enumerate(fsf_file_template) if "set fmri(npts)" in e]
    if l1_block['ImageIncludeList'] is not "" and l1_block['ImageExcludeList'] is not "":
        raise ValueError("Only one of ImageIncludeList and ImageExcludeList should be non-empty")

    image_files = glob.glob(os.path.join(l1_block['TargetDirectory'], "**", "*"+l1_block['TargetSuffix']), recursive = True)

    if l1_block['ImageIncludeList'] is not "":
        image_files = [file_path for file_path in image_files if os.path.basename(file_path) in l1_block['ImageIncludeList']]
        base_names = [os.path.basename(file_path) for file_path in image_files]

        files_not_found = [file for file in base_names if file not in l1_block['ImageIncludeList']]
        if len(files_not_found):
            logger.warning("Did not find the following files: " + str(files_not_found))

    if l1_block['ImageExcludeList'] is not "":
        image_files = [file_path for file_path in image_files if
                       os.path.basename(file_path) not in l1_block['ImageExcludeList']]

    image_files = [file for file in image_files if
                         "task-" + glm_setup_options["TaskName"] in file]

    if not os.path.exists(l1_block['FSFDir']):
        os.mkdir(l1_block['FSFDir'])
    for file in image_files:
        try:
            logger.debug("Creating FSF File for image:" + os.path.basename(file))
            img_data = nib.load(file)
            total_tps = img_data.shape[3]
            ev_conf = _get_ev_confound_mat(file, l1_block, logger)
            out_dir = os.path.join(l1_block['OutputDir'],os.path.basename(file).replace(l1_block["TargetSuffix"], ".feat"))
            out_fsf = os.path.join(l1_block['FSFDir'],
                                   os.path.basename(file).replace(l1_block["TargetSuffix"], ".fsf"))
            new_fsf = fsf_file_template

            new_fsf[tps_inds[0]] = "set fmri(npts) " + str(total_tps) + "\n"
            new_fsf[output_ind[0]] = "set fmri(outputdir) \"" + os.path.abspath(out_dir) + "\"\n"
            new_fsf[image_files_ind[0]] = "set feat_files(1) \"" + os.path.abspath(file) + "\"\n"

            if glm_setup_options['ReferenceImage'] is not "":
                new_fsf[regstandard_ind[0]] = "set fmri(regstandard) \"" + os.path.abspath(glm_setup_options['ReferenceImage']) + "\"\n"
            if l1_block['ConfoundSuffix'] is not "":
                new_fsf[confound_file_ind[0]] = "set confoundev_files(1) \"" + os.path.abspath(ev_conf['Confounds']) + "\"\n"

            for i, e in enumerate(ev_conf['EVs']):
                new_fsf[ev_file_inds[i]] = "set fmri(custom" + str(i +1) + ") \"" + os.path.abspath(e) + "\"\n"

            with open(out_fsf, "w") as fsf_file:
                fsf_file.writelines(new_fsf)

        except (EVFileNotFoundError, ConfoundsNotFoundError) as nfe:
            logger.warn(nfe)


def _get_ev_confound_mat(file, l1_block, logger):

    file_name = os.path.basename(file)

    file_prefix = os.path.basename(file).replace(l1_block["TargetSuffix"], "")

    EV_files = []
    for EV in l1_block['EVFileSuffices']:
        try:
            search_path = os.path.join(l1_block["EVDirectory"],"**",file_prefix + EV)
            logger.debug(f"EV search path: {search_path}")
            search_results = glob.glob((search_path), recursive = True)
            if len(search_results) < 1:
                raise EVFileNotFoundError(f"EV file not found: {EV}")
            elif len(search_results) > 1:
                raise EVFileNotFoundError(f"Found more than one EV file matching pattern: {search_path}")
            EV_files.append(search_results[0])
        except EVFileNotFoundError as evfnfe:
            logger.debug(evfnfe)

    if len(EV_files) is not len(l1_block['EVFileSuffices']):
        raise EVFileNotFoundError((
            f"Did not find enough EV files for image: {file_name}. "
            f"Only found {len(EV_files)} and need "
            f"{len(l1_block['EVFileSuffices'])}"
        ))

    if l1_block["ConfoundSuffix"] is not "":
        search_path = os.path.join(l1_block["ConfoundDirectory"],"**",
            file_prefix + l1_block['ConfoundSuffix'])
        logger.debug(f"Confound search path: {search_path}")
        search_results = glob.glob((search_path), recursive = True)
        if len(search_results) < 1:
            raise ConfoundsNotFoundError(f"Did not find a confound file for image: {file_name}")
        elif len(search_results) > 1:
            raise ConfoundsNotFoundError(f"Found more than one confounds file matching pattern: {search_path}")
        return {"EVs": EV_files, "Confounds": search_results[0]}

    return {"EVs": EV_files}



